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
)

from config import BOT_TOKEN
import storage
import engine
import combat as C
from memory import new_world
from character import new_character, CLASSES

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Setup(StatesGroup):
    setting = State()
    name = State()
    personality = State()


# ---------- Клавиатуры ----------
CONTINUE_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="▶️ Продолжить", callback_data="continue"),
    InlineKeyboardButton(text="🔄 Новая игра", callback_data="restart"),
]])

CLASS_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⚔️ Воин", callback_data="class_warrior"),
     InlineKeyboardButton(text="🔮 Маг", callback_data="class_mage")],
    [InlineKeyboardButton(text="🗡 Плут", callback_data="class_rogue"),
     InlineKeyboardButton(text="✨ Жрец", callback_data="class_cleric")],
])

COMBAT_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="⚔️ Атака", callback_data="combat_attack"),
]])


def roll_kb(stat: str, difficulty: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"🎲 Бросок {stat} (сл. {difficulty})",
            callback_data="roll",
        )
    ]])


# ---------- /start ----------
@dp.message(Command("start"))
async def cmd_start(m: Message, state: FSMContext):
    await state.clear()
    existing = storage.load(m.from_user.id)
    if existing and existing["character"]:
        await m.answer("У тебя есть сохранённая партия.", reply_markup=CONTINUE_KB)
        return
    await m.answer("Новая игра.\n\nОпиши **сеттинг** мира (эпоха, жанр, атмосфера):")
    await state.set_state(Setup.setting)


@dp.callback_query(F.data == "continue")
async def cb_continue(cb: CallbackQuery):
    await cb.message.answer("Продолжаем. Что делаешь?")
    await cb.answer()


@dp.callback_query(F.data == "restart")
async def cb_restart(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Опиши **сеттинг** мира:")
    await state.set_state(Setup.setting)
    await cb.answer()


# ---------- Создание персонажа ----------
@dp.message(Setup.setting, F.text)
async def setup_setting(m: Message, state: FSMContext):
    await state.update_data(setting=m.text.strip())
    await m.answer("Как зовут твоего персонажа?")
    await state.set_state(Setup.name)


@dp.message(Setup.name, F.text)
async def setup_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await m.answer("Опиши **характер** персонажа (пара фраз):")
    await state.set_state(Setup.personality)


@dp.message(Setup.personality, F.text)
async def setup_personality(m: Message, state: FSMContext):
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
        f"Мир создан. {data['name']} входит в историю."
    )
    await cb.answer()


# ---------- Бросок кубика ----------
@dp.callback_query(F.data == "roll")
async def cb_roll(cb: CallbackQuery):
    world = storage.load(cb.from_user.id)
    if not world or not world.get("pending"):
        await cb.answer("Бросать нечего.", show_alert=True)
        return
    result = engine.resolve_check(world, {})
    storage.save(cb.from_user.id, world)
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer(result["text"])
    await cb.answer()


# ---------- Боевые кнопки ----------
@dp.callback_query(F.data == "combat_attack")
async def cb_attack(cb: CallbackQuery):
    world = storage.load(cb.from_user.id)
    if not world or not (world.get("combat") or {}).get("active"):
        await cb.answer("Ты не в бою.", show_alert=True)
        return

    lines = [C.player_attack(world)]

    if not C.combat_over(world):
        enemy_log = C.enemy_turn(world)
        if enemy_log:
            lines.append(enemy_log)

    storage.save(cb.from_user.id, world)
    text = "\n\n".join(lines)
    status = C.status_line(world)
    if status:
        text += f"\n\n{status}"

    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if C.combat_over(world):
        if world["character"]["hp"] <= 0:
            text += "\n\n☠️ Ты повержен. Напиши /start, чтобы начать заново."
            C.end_combat(world)
            storage.save(cb.from_user.id, world)
            await cb.message.answer(text)
        else:
            summary = C.end_combat(world)
            text += f"\n\n✅ {summary}"
            storage.save(cb.from_user.id, world)
            try:
                result = await engine.process_action(
                    world, "[бой окончен, продолжаю]"
                )
                text += f"\n\n{result['text']}"
                storage.save(cb.from_user.id, world)
            except Exception as e:
                logging.exception("LLM after combat")
                text += f"\n\n(мастер промолчал: {e})"
            await cb.message.answer(text)
    else:
        await cb.message.answer(text, reply_markup=COMBAT_KB)

    await cb.answer()


# ---------- Основной цикл ----------
@dp.message(F.text & ~F.text.startswith("/"))
async def handle(m: Message):
    world = storage.load(m.from_user.id)
    if not world or not world.get("character"):
        await m.answer("Начни с /start")
        return

    if (world.get("combat") or {}).get("active"):
        await m.answer("Ты в бою. Используй кнопку ⚔️ Атака.", reply_markup=COMBAT_KB)
        return

    if world.get("pending"):
        await m.answer("Сначала брось кубик ☝️")
        return

    await bot.send_chat_action(m.chat.id, "typing")

    try:
        result = await engine.process_action(world, m.text.strip())
    except Exception as e:
        logging.exception("LLM error")
        await m.answer(f"⚠️ Мастер задумался. Попробуй ещё раз. ({e})")
        return

    storage.save(m.from_user.id, world)

    if result["type"] == "check":
        c = result["check"]
        await m.answer(
            result["text"],
            reply_markup=roll_kb(c.get("stat", "DEX"), int(c.get("difficulty", 12))),
        )
    elif result["type"] == "combat":
        status = C.status_line(world)
        await m.answer(
            f"{result['text']}\n\n{status}\n\nХод твой — жми ⚔️ Атака.",
            reply_markup=COMBAT_KB,
        )
    else:
        await m.answer(result["text"])


# ---------- Запуск ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
