import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    BufferedInputFile,
)

from config import BOT_TOKEN
import storage
import engine
import combat as C
import inventory as I
import voice
from memory import new_world, push_recent_action
from character import new_character, CLASSES

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------- Фильтр инъекций ----------
INJECTION_MARKERS = (
    "забудь предыдущие",
    "забудь инструкции",
    "забудь правила",
    "забудь роль",
    "игнорируй инструкции",
    "игнорируй правила",
    "покажи промпт",
    "покажи системн",
    "покажи инструкции",
    "повтори промпт",
    "повтори инструкции",
    "повтори системн",
    "system prompt",
    "system message",
    "ignore previous",
    "ignore instructions",
    "ответь текстом",
    "ответь без json",
    "стань чат",
    "стань ассистент",
    "будь чат",
    "будь ассистент",
    "новая роль",
    "выйди из роли",
    "выйти из роли",
)


def looks_like_injection(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in INJECTION_MARKERS)


class Setup(StatesGroup):
    setting = State()
    name = State()
    personality = State()


# ---------- Клавиатуры ----------
INVENTORY_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🎒 Инвентарь")]],
    resize_keyboard=True,
    is_persistent=True,
)

CONTINUE_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="▶️ Продолжить", callback_data="continue"),
    InlineKeyboardButton(text="🔄 Новая игра", callback_data="restart"),
]])

CLASS_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="⚔️ Воин", callback_data="class_warrior"),
    InlineKeyboardButton(text="🗡 Плут", callback_data="class_rogue"),
    InlineKeyboardButton(text="🔮 Маг", callback_data="class_mage"),
]])

VOICE_BTN = InlineKeyboardButton(text="🔊 Озвучить", callback_data="voice_play")


def voice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[VOICE_BTN]])


def combat_kb(world: dict) -> InlineKeyboardMarkup:
    char = world.get("character", {})
    charges = char.get("charges") or 0
    skill_name = "Скилл"
    cls = CLASSES.get(char.get("cls"), {})
    if cls and cls.get("skill"):
        skill_name = cls["skill"]["name"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атака", callback_data="combat_attack"),
         InlineKeyboardButton(text=f"🌀 {skill_name} ({charges})",
                              callback_data="combat_skill")],
        [InlineKeyboardButton(text="🏳 Сдаться", callback_data="combat_flee")],
        [VOICE_BTN],
    ])


def roll_kb(stat: str, difficulty: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎲 Бросок {stat} (сл. {difficulty})",
            callback_data="roll",
        )],
        [VOICE_BTN],
    ])


def inventory_kb(world: dict) -> InlineKeyboardMarkup:
    inv = world["character"].get("inventory", [])
    rows = []
    for i, item in enumerate(inv):
        rows.append([InlineKeyboardButton(
            text=I.format_item_line(item),
            callback_data=f"inv_{i}",
        )])
    rows.append([InlineKeyboardButton(text="✖️ Закрыть", callback_data="inv_close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def item_kb(idx: int, item: dict, char: dict) -> InlineKeyboardMarkup:
    rows = []
    if item.get("type") == "potion":
        rows.append([InlineKeyboardButton(text="✅ Использовать",
                                          callback_data=f"inv_use_{idx}")])
    if I.can_upgrade(item):
        cost = I.upgrade_cost(item)
        shards = char.get("shards", 0)
        if shards >= cost:
            label = f"⚒ Улучшить ({cost} 🔹)"
        else:
            label = f"⚒ Нужно {cost} 🔹"
        rows.append([InlineKeyboardButton(text=label,
                                          callback_data=f"inv_upgrade_{idx}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад",
                                      callback_data="inv_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _safe_int(value, default: int) -> int:
    try:
        return int(float(str(value).replace("%", "").strip()))
    except (ValueError, TypeError):
        return default


def _with_epilogue(world: dict, text: str) -> str:
    """Добавляет счётчик эпилога или пометку о завершении."""
    w = world.get("world", {})
    if w.get("final_reached"):
        return text + "\n\n🏁 **История завершена.** Напиши /start, чтобы начать новую."
    epilogue = w.get("epilogue_turns", 0)
    if epilogue > 0:
        return text + f"\n\n⏳ Эпилог: осталось {epilogue} ходов."
    return text


# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    existing = storage.load(m.from_user.id)
    if existing and existing.get("character"):
        await m.answer("У тебя есть сохранённая партия.",
                       reply_markup=INVENTORY_KB)
        await m.answer("Выбери действие:", reply_markup=CONTINUE_KB)
        return
    await m.answer(
        "Новая игра.\n\nОпиши **сеттинг** мира (эпоха, жанр, атмосфера):",
        reply_markup=INVENTORY_KB,
    )
    await state.set_state(Setup.setting)


@dp.callback_query(F.data == "continue")
async def cb_continue(cb: CallbackQuery):
    await cb.message.answer("Продолжаем. Что делаешь?", reply_markup=INVENTORY_KB)
    await cb.answer()


@dp.callback_query(F.data == "restart")
async def cb_restart(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Опиши **сеттинг** мира:", reply_markup=INVENTORY_KB)
    await state.set_state(Setup.setting)
    await cb.answer()


# ---------- Создание персонажа ----------
@dp.message(Setup.setting, F.text)
async def setup_setting(m: Message, state: FSMContext):
    if m.text == "🎒 Инвентарь":
        await m.answer("Сначала закончим создание персонажа.")
        return
    await state.update_data(setting=m.text.strip())
    await m.answer("Как зовут твоего персонажа?")
    await state.set_state(Setup.name)


@dp.message(Setup.name, F.text)
async def setup_name(m: Message, state: FSMContext):
    if m.text == "🎒 Инвентарь":
        await m.answer("Сначала закончим создание персонажа.")
        return
    await state.update_data(name=m.text.strip())
    await m.answer(
        "Расскажи коротко о своём персонаже — кто он, откуда, как выглядит, "
        "какой у него характер и что важно знать. Пара-тройка предложений.\n\n"
        "_Это описание мастер будет использовать в сценах._",
        parse_mode="Markdown",
    )
    await state.set_state(Setup.personality)


@dp.message(Setup.personality, F.text)
async def setup_personality(m: Message, state: FSMContext):
    if m.text == "🎒 Инвентарь":
        await m.answer("Сначала закончим создание персонажа.")
        return
    await state.update_data(personality=m.text.strip())
    await m.answer("Выбери **класс**:", reply_markup=CLASS_KB)


@dp.callback_query(F.data.startswith("class_"))
async def cb_class(cb: CallbackQuery, state: FSMContext):
    cls_key = cb.data.replace("class_", "")
    if cls_key not in CLASSES:
        await cb.answer("Нет такого класса.", show_alert=True)
        return

    data = await state.get_data()
    if not data.get("setting") or not data.get("name") or not data.get("personality"):
        await cb.answer("Сессия создания истекла. Напиши /start", show_alert=True)
        await state.clear()
        return

    await state.clear()

    world = new_world(cb.from_user.id)
    world["world"]["setting"] = data["setting"]
    world["world"]["tone"] = "тёмное фэнтези"
    world["world"]["milestone"] = "Пролог"
    world["character"] = new_character(data["name"], data["personality"], cls_key)

    storage.save(cb.from_user.id, world)
    cls = CLASSES[cls_key]
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await cb.message.answer(
        f"Класс: {cls['name']}.\n{cls['desc']}\n\n"
        f"Скилл: {cls['skill']['name']} — {cls['skill']['desc']}.",
        reply_markup=INVENTORY_KB,
    )

    await cb.message.answer("Создаю мир и начинаю историю…")
    await bot.send_chat_action(cb.message.chat.id, "typing")

    try:
        result = await engine.process_action(
            world,
            "[Начало игры. Сначала придумай ФИНАЛ всей истории — что должно "
            "случиться в конце, к чему всё идёт. Сохрани в memory.world.final "
            "(1-3 предложения). Затем опиши стартовую сцену: где герой, что "
            "он видит, завязка сюжета. Финал в narrative НЕ раскрывай. "
            "Закончи на крючке.]"
        )
        world["last_narrative"] = result["text"]
        storage.save(cb.from_user.id, world)

        if result["type"] == "check":
            c = result["check"]
            difficulty = _safe_int(c.get("difficulty", 12), 12)
            await cb.message.answer(
                _with_epilogue(world, result["text"]),
                reply_markup=roll_kb(c.get("stat", "DEX"), difficulty),
            )
        elif result["type"] == "combat":
            status = C.status_line(world)
            await cb.message.answer(
                f"{_with_epilogue(world, result['text'])}\n\n{status}",
                reply_markup=combat_kb(world),
            )
        else:
            await cb.message.answer(
                _with_epilogue(world, result["text"]),
                reply_markup=voice_kb(),
            )
    except Exception as e:
        logging.exception("LLM start scene error")
        await cb.message.answer(
            "⚠️ Мастер задумался на старте. Напиши любое действие, чтобы начать."
        )

    await cb.answer()


# ---------- Озвучка ----------
@dp.callback_query(F.data == "voice_play")
async def cb_voice(cb: CallbackQuery):
    await cb.answer("Готовлю озвучку…")

    world = storage.load(cb.from_user.id)
    if not world:
        return

    text = world.get("last_narrative")
    if not text:
        await cb.message.answer("Нечего озвучивать.")
        return

    await bot.send_chat_action(cb.message.chat.id, "record_voice")
    try:
        audio_bytes, truncated = await voice.synthesize(text)
    except Exception as e:
        logging.exception("voice error")
        await cb.message.answer("⚠️ Ошибка озвучки. Попробуй позже.")
        return

    voice_file = BufferedInputFile(audio_bytes, filename="scene.ogg")
    await cb.message.answer_voice(voice_file)

    if truncated:
        await cb.message.answer("_(текст обрезан — сцена слишком длинная)_",
                                parse_mode="Markdown")


# ---------- Бросок кубика ----------
@dp.callback_query(F.data == "roll")
async def cb_roll(cb: CallbackQuery):
    await cb.answer()
    world = storage.load(cb.from_user.id)
    if not world or not world.get("pending"):
        await cb.message.answer("Бросать нечего.")
        return

    await bot.send_chat_action(cb.message.chat.id, "typing")
    result = await engine.resolve_check(world)
    world["last_narrative"] = result["text"]
    storage.save(cb.from_user.id, world)

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    display = _with_epilogue(world, result["text"])

    if result["type"] == "check":
        c = result["check"]
        difficulty = _safe_int(c.get("difficulty", 12), 12)
        await cb.message.answer(
            display,
            reply_markup=roll_kb(c.get("stat", "DEX"), difficulty),
        )
    elif result["type"] == "combat":
        status = C.status_line(world)
        await cb.message.answer(
            f"{display}\n\n{status}",
            reply_markup=combat_kb(world),
        )
    else:
        await cb.message.answer(display, reply_markup=voice_kb())


# ---------- Инвентарь ----------
@dp.message(F.text == "🎒 Инвентарь")
async def btn_inventory(m: Message):
    world = storage.load(m.from_user.id)
    if not world or not world.get("character"):
        await m.answer("Начни с /start")
        return
    inv = world["character"].get("inventory", [])
    shards = world["character"].get("shards", 0)
    if not inv:
        await m.answer(f"🎒 Инвентарь пуст. 🔹 Осколки: {shards}")
        return
    await m.answer(
        f"🎒 **Инвентарь**  |  🔹 Осколки: {shards}\nВыбери предмет:",
        parse_mode="Markdown",
        reply_markup=inventory_kb(world),
    )


@dp.callback_query(F.data == "inv_open")
async def cb_inv_open(cb: CallbackQuery):
    await cb.answer()
    world = storage.load(cb.from_user.id)
    if not world or not world.get("character"):
        return
    inv = world["character"].get("inventory", [])
    shards = world["character"].get("shards", 0)
    if not inv:
        try:
            await cb.message.edit_text(f"🎒 Инвентарь пуст. 🔹 Осколки: {shards}")
        except Exception:
            pass
        return
    try:
        await cb.message.edit_text(
            f"🎒 **Инвентарь**  |  🔹 Осколки: {shards}\nВыбери предмет:",
            parse_mode="Markdown",
            reply_markup=inventory_kb(world),
        )
    except Exception:
        pass


@dp.callback_query(F.data == "inv_close")
async def cb_inv_close(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.delete()
    except Exception:
        pass


@dp.callback_query(F.data.startswith("inv_use_"))
async def cb_inv_use(cb: CallbackQuery):
    await cb.answer()
    world = storage.load(cb.from_user.id)
    if not world or not world.get("character"):
        return

    if world.get("pending"):
        await cb.message.answer("Сначала брось кубик ☝️")
        return

    try:
        idx = int(cb.data.replace("inv_use_", ""))
    except ValueError:
        return

    inv = world["character"].get("inventory", [])
    if idx < 0 or idx >= len(inv):
        await cb.message.answer("Предмет исчез.")
        return

    item_name = inv[idx].get("name", "предмет")

    result_text = I.use_potion(world["character"], idx)
    in_combat = (world.get("combat") or {}).get("active")

    if "HP:" in result_text:
        char = world["character"]
        push_recent_action(
            world,
            f"Использовано «{item_name}». HP сейчас: {char['hp']}/{char['hp_max']}."
        )

    if in_combat and not C.combat_over(world):
        enemy_log = C.enemy_turn(world)
        if enemy_log:
            result_text += "\n\n" + enemy_log

    storage.save(cb.from_user.id, world)

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if in_combat and C.combat_over(world):
        if world["character"]["hp"] <= 0:
            result_text += "\n\n☠️ Ты повержен. Напиши /start, чтобы начать заново."
            C.end_combat(world)
            world["last_narrative"] = result_text
            storage.save(cb.from_user.id, world)
            await cb.message.answer(_with_epilogue(world, result_text))
            return
        summary, level_msgs = C.end_combat(world)
        result_text += f"\n\n✅ {summary}\n❤️ HP восстановлен."
        if level_msgs:
            result_text += "\n\n" + "\n".join(level_msgs)
        world["last_narrative"] = result_text
        storage.save(cb.from_user.id, world)
        await cb.message.answer(_with_epilogue(world, result_text))
        await bot.send_chat_action(cb.message.chat.id, "typing")
        try:
            result = await engine.process_action(world, "[бой окончен, продолжаю]")
            world["last_narrative"] = result["text"]
            storage.save(cb.from_user.id, world)
            await cb.message.answer(
                _with_epilogue(world, result["text"]),
                reply_markup=voice_kb(),
            )
        except Exception as e:
            logging.exception("LLM after combat")
            await cb.message.answer("(мастер промолчал)")
        return

    world["last_narrative"] = result_text
    storage.save(cb.from_user.id, world)

    if in_combat:
        await cb.message.answer(_with_epilogue(world, result_text),
                                reply_markup=combat_kb(world))
    else:
        await cb.message.answer(_with_epilogue(world, result_text),
                                reply_markup=INVENTORY_KB)


@dp.callback_query(F.data.startswith("inv_upgrade_"))
async def cb_inv_upgrade(cb: CallbackQuery):
    await cb.answer()
    world = storage.load(cb.from_user.id)
    if not world or not world.get("character"):
        return
    try:
        idx = int(cb.data.replace("inv_upgrade_", ""))
    except ValueError:
        return

    result = I.upgrade_item(world["character"], idx)
    storage.save(cb.from_user.id, world)

    inv = world["character"].get("inventory", [])
    if 0 <= idx < len(inv):
        item = inv[idx]
        try:
            await cb.message.edit_text(
                result + "\n\n" + I.item_info(item),
                reply_markup=item_kb(idx, item, world["character"]),
            )
        except Exception:
            await cb.message.answer(result)
    else:
        await cb.message.answer(result)


@dp.callback_query(F.data.startswith("inv_"))
async def cb_inv_item(cb: CallbackQuery):
    suffix = cb.data.replace("inv_", "")
    if suffix in ("open", "close") or suffix.startswith("use_") or suffix.startswith("upgrade_"):
        return
    try:
        idx = int(suffix)
    except ValueError:
        await cb.answer()
        return

    await cb.answer()
    world = storage.load(cb.from_user.id)
    if not world or not world.get("character"):
        return
    inv = world["character"].get("inventory", [])
    if idx < 0 or idx >= len(inv):
        await cb.message.answer("Предмет исчез.")
        return

    item = inv[idx]
    text = I.item_info(item)
    try:
        await cb.message.edit_text(
            text,
            reply_markup=item_kb(idx, item, world["character"]),
        )
    except Exception:
        pass


# ---------- Бой: атака ----------
@dp.callback_query(F.data == "combat_attack")
async def cb_attack(cb: CallbackQuery):
    await cb.answer()

    world = storage.load(cb.from_user.id)
    if not world or not (world.get("combat") or {}).get("active"):
        await cb.message.answer("Ты не в бою.")
        return

    try:
        lines = [C.player_attack(world)]
        if not C.combat_over(world):
            enemy_log = C.enemy_turn(world)
            if enemy_log:
                lines.append(enemy_log)
    except Exception as e:
        logging.exception("combat error")
        try:
            C.end_combat(world)
        except Exception:
            world["combat"] = {"active": False, "enemies": [], "log": []}
        storage.save(cb.from_user.id, world)
        await cb.message.answer("⚠️ Ошибка боя. Бой сброшен.")
        return

    storage.save(cb.from_user.id, world)
    text = "\n\n".join(lines)
    status = C.status_line(world)
    if status:
        text += f"\n\n{status}"

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _finish_turn(cb, world, text)


# ---------- Бой: скилл ----------
@dp.callback_query(F.data == "combat_skill")
async def cb_skill(cb: CallbackQuery):
    await cb.answer()

    world = storage.load(cb.from_user.id)
    if not world or not (world.get("combat") or {}).get("active"):
        await cb.message.answer("Ты не в бою.")
        return

    char = world["character"]
    if char.get("charges", 0) <= 0:
        await cb.message.answer("Зарядов скилла нет. Отдохни или бей обычной атакой.")
        return

    try:
        lines = [C.player_skill(world)]
        if not C.combat_over(world):
            enemy_log = C.enemy_turn(world)
            if enemy_log:
                lines.append(enemy_log)
    except Exception as e:
        logging.exception("skill error")
        try:
            C.end_combat(world)
        except Exception:
            world["combat"] = {"active": False, "enemies": [], "log": []}
        storage.save(cb.from_user.id, world)
        await cb.message.answer("⚠️ Ошибка скилла. Бой сброшен.")
        return

    storage.save(cb.from_user.id, world)
    text = "\n\n".join(lines)
    status = C.status_line(world)
    if status:
        text += f"\n\n{status}"

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _finish_turn(cb, world, text)


async def _finish_turn(cb: CallbackQuery, world: dict, text: str):
    if not C.combat_over(world):
        await cb.message.answer(text, reply_markup=combat_kb(world))
        return

    if world["character"]["hp"] <= 0:
        text += "\n\n☠️ Ты повержен. Напиши /start, чтобы начать заново."
        C.end_combat(world)
        world["last_narrative"] = text
        storage.save(cb.from_user.id, world)
        await cb.message.answer(_with_epilogue(world, text))
        return

    summary, level_msgs = C.end_combat(world)
    text += f"\n\n✅ {summary}\n❤️ HP восстановлен."
    if level_msgs:
        text += "\n\n" + "\n".join(level_msgs)
    world["last_narrative"] = text
    storage.save(cb.from_user.id, world)
    await cb.message.answer(_with_epilogue(world, text))

    await bot.send_chat_action(cb.message.chat.id, "typing")
    try:
        result = await engine.process_action(world, "[бой окончен, продолжаю]")
        world["last_narrative"] = result["text"]
        storage.save(cb.from_user.id, world)
        await cb.message.answer(
            _with_epilogue(world, result["text"]),
            reply_markup=voice_kb(),
        )
    except Exception as e:
        logging.exception("LLM after combat")
        await cb.message.answer("(мастер промолчал)")


# ---------- Бой: сдаться ----------
@dp.callback_query(F.data == "combat_flee")
async def cb_flee(cb: CallbackQuery):
    await cb.answer()

    world = storage.load(cb.from_user.id)
    if not world or not (world.get("combat") or {}).get("active"):
        await cb.message.answer("Ты не в бою.")
        return

    C.end_combat(world)
    storage.save(cb.from_user.id, world)

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await cb.message.answer("🏳 Ты отступаешь. Бой прерван, HP восстановлен.")

    await bot.send_chat_action(cb.message.chat.id, "typing")
    try:
        result = await engine.process_action(
            world,
            "[Игрок сбежал из боя. Опиши последствия отступления: куда он "
            "бежит, что происходит вокруг, кто преследует. Продолжи сюжет.]"
        )
        world["last_narrative"] = result["text"]
        storage.save(cb.from_user.id, world)
        await cb.message.answer(
            _with_epilogue(world, result["text"]),
            reply_markup=voice_kb(),
        )
    except Exception as e:
        logging.exception("LLM after flee")
        await cb.message.answer("(мастер промолчал)")


# ---------- Команда /flee ----------
@dp.message(Command("flee"))
async def cmd_flee(m: Message):
    world = storage.load(m.from_user.id)
    if not world or not (world.get("combat") or {}).get("active"):
        await m.answer("Ты не в бою.")
        return
    C.end_combat(world)
    storage.save(m.from_user.id, world)
    await m.answer("🏳 Ты выходишь из боя. HP восстановлен.")

    await bot.send_chat_action(m.chat.id, "typing")
    try:
        result = await engine.process_action(
            world,
            "[Игрок сбежал из боя. Опиши последствия отступления, продолжи сюжет.]"
        )
        world["last_narrative"] = result["text"]
        storage.save(m.from_user.id, world)
        await m.answer(
            _with_epilogue(world, result["text"]),
            reply_markup=voice_kb(),
        )
    except Exception as e:
        logging.exception("LLM after flee")
        await m.answer("(мастер промолчал)")


# ---------- Основной цикл ----------
@dp.message(F.text & ~F.text.startswith("/"))
async def handle(m: Message):
    world = storage.load(m.from_user.id)
    if not world or not world.get("character"):
        await m.answer("Начни с /start")
        return

    if world["world"].get("final_reached"):
        await m.answer("🏁 История завершена. Напиши /start, чтобы начать новую.")
        return

    if looks_like_injection(m.text):
        await m.answer(
            "Мастер не отвечает на такие просьбы. Опиши, что делает персонаж."
        )
        return

    if (world.get("combat") or {}).get("active"):
        await m.answer(
            "Ты в бою. Жми ⚔️ Атака или 🌀 Скилл.",
            reply_markup=combat_kb(world),
        )
        return

    if world.get("pending"):
        c = world["pending"].get("check") or {}
        difficulty = _safe_int(c.get("difficulty", 12), 12)
        await m.answer(
            "Сначала брось кубик ☝️",
            reply_markup=roll_kb(c.get("stat", "DEX"), difficulty),
        )
        return

    await bot.send_chat_action(m.chat.id, "typing")

    try:
        result = await engine.process_action(world, m.text.strip())
    except Exception as e:
        logging.exception("LLM error")
        await m.answer("⚠️ Мастер задумался. Попробуй ещё раз.")
        return

    world["last_narrative"] = result["text"]
    storage.save(m.from_user.id, world)

    display = _with_epilogue(world, result["text"])

    if result["type"] == "check":
        c = result["check"]
        difficulty = _safe_int(c.get("difficulty", 12), 12)
        await m.answer(
            display,
            reply_markup=roll_kb(c.get("stat", "DEX"), difficulty),
        )
    elif result["type"] == "combat":
        status = C.status_line(world)
        await m.answer(
            f"{display}\n\n{status}",
            reply_markup=combat_kb(world),
        )
    else:
        await m.answer(display, reply_markup=voice_kb())


# ---------- Запуск ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
