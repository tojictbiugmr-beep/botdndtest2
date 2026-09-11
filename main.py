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
from memory import new_world
from character import new_character

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
    data = await state.get_data()
    await state.clear()

    world = new_world(m.from_user.id)
    world["world"]["setting"] = data["setting"]
    world["world"]["tone"] = "тёмное фэнтези"
    world["world"]["milestone"] = "Пролог"
    world["character"] = new_character(data["name"], m.text.strip())

    storage.save(m.from_user.id, world)
    await m.answer(
        f"Мир создан. {data['name']} входит в историю.\n"
        f"Опиши первое действие или попроси мастера начать сцену."
    )


# ---------- Бросок кубика (только когда ждёт проверка) ----------
@dp.callback_query(F.data == "roll")
async def cb_roll(cb: CallbackQuery):
    world = storage.load(cb.from_user.id)
    if not world or not world.get("pending"):
        await cb.answer("Бросать нечего.", show_alert=True)
        return

    result = engine.resolve_check(world, {})
    storage.save(cb.from_user.id, world)

    # убираем кнопку с исходного сообщения
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await cb.message.answer(result["text"])
    await cb.answer()


# ---------- Основной игровой цикл ----------
@dp.message(F.text & ~F.text.startswith("/"))
async def handle(m: Message):
    world = storage.load(m.from_user.id)
    if not world or not world.get("character"):
        await m.answer("Начни с /start")
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
    else:
        await m.answer(result["text"])


# ---------- Запуск ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
