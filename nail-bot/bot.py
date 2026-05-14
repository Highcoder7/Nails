import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from openai import AsyncOpenAI

import config
import prompts

# --- Config & Initialization ---
logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# --- FSM States ---
class CaptionStates(StatesGroup):
    waiting_for_design = State()
    waiting_for_shape = State()
    waiting_for_length = State()

class ReelsStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_psychotype = State()

# --- Keyboards ---
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Подпись к фото")],
            [KeyboardButton(text="🎬 Сценарий Reels")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_cancel_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    return keyboard

def get_reels_psycho_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Убедить (Логик)"), KeyboardButton(text="💖 Вдохновить (Эмоционал)")],
            [KeyboardButton(text="⚡ Продать (Практик)"), KeyboardButton(text="🔥 В тренд (Социальщик)")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_caption_design_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Nude"), KeyboardButton(text="Яркий")],
            [KeyboardButton(text="Френч"), KeyboardButton(text="Арт (Дизайн)")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_caption_shape_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Миндаль"), KeyboardButton(text="Квадрат")],
            [KeyboardButton(text="Овал"), KeyboardButton(text="Балерина (Coffin)")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_caption_length_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Короткая"), KeyboardButton(text="Средняя"), KeyboardButton(text="Длинная")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_retry_inline_keyboard(action_type):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сгенерировать ещё раз", callback_data=f"retry_{action_type}")]
        ]
    )

# --- Handlers ---

@dp.message(Command("start", "menu"))
async def cmd_start_menu(message: types.Message, state: FSMContext):
    await state.set_state(None) # Clear state but keep data
    await message.answer(
        "Привет! Я бот для генерации контента для ногтевого салона.\nВыберите действие ниже:",
        reply_markup=get_main_menu()
    )

@dp.message(F.text.lower() == "отмена")
async def action_cancel(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer("Действие отменено. Возврат в главное меню.", reply_markup=get_main_menu())

# --- Photo Caption Flow ---

@dp.message(F.text == "📸 Подпись к фото")
async def caption_start(message: types.Message, state: FSMContext):
    await state.set_state(CaptionStates.waiting_for_design)
    await message.answer("Выберите тип дизайна:", reply_markup=get_caption_design_menu())

# --- Reels Script Flow ---

@dp.message(F.text == "🎬 Сценарий Reels")
async def reels_start(message: types.Message, state: FSMContext):
    await state.set_state(ReelsStates.waiting_for_description)
    await message.answer("Опишите работу (свободный текст):", reply_markup=get_cancel_menu())

# --- Caption FSM State Handlers ---

VALID_DESIGNS = {"Nude", "Яркий", "Френч", "Арт (Дизайн)"}
VALID_SHAPES = {"Миндаль", "Квадрат", "Овал", "Балерина (Coffin)"}
VALID_LENGTHS = {"Короткая", "Средняя", "Длинная"}

@dp.message(CaptionStates.waiting_for_design)
async def caption_design(message: types.Message, state: FSMContext):
    if message.text not in VALID_DESIGNS:
        await message.answer("Пожалуйста, выберите один из вариантов на клавиатуре.", reply_markup=get_caption_design_menu())
        return
    await state.update_data(design=message.text)
    await state.set_state(CaptionStates.waiting_for_shape)
    await message.answer("Выберите форму ногтей:", reply_markup=get_caption_shape_menu())

@dp.message(CaptionStates.waiting_for_shape)
async def caption_shape(message: types.Message, state: FSMContext):
    if message.text not in VALID_SHAPES:
        await message.answer("Пожалуйста, выберите один из вариантов на клавиатуре.", reply_markup=get_caption_shape_menu())
        return
    await state.update_data(shape=message.text)
    await state.set_state(CaptionStates.waiting_for_length)
    await message.answer("Выберите длину ногтей:", reply_markup=get_caption_length_menu())

@dp.message(CaptionStates.waiting_for_length)
async def caption_length(message: types.Message, state: FSMContext):
    if message.text not in VALID_LENGTHS:
        await message.answer("Пожалуйста, выберите один из вариантов на клавиатуре.", reply_markup=get_caption_length_menu())
        return
    await state.update_data(length=message.text)
    data = await state.get_data()

    await message.answer("Генерирую подпись... ⏳", reply_markup=get_main_menu())
    await generate_caption(message, data["design"], data["shape"], data["length"])
    await state.set_state(None)

async def generate_caption(message: types.Message, design: str, shape: str, length: str):
    user_prompt = prompts.CAPTION_USER_PROMPT.format(design=design, shape=shape, length=length)
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompts.CAPTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        result_text = response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        await message.answer("Произошла ошибка при генерации текста. Пожалуйста, попробуйте позже.")
        return

    await message.answer(result_text, reply_markup=get_retry_inline_keyboard("caption"))

# --- Reels FSM State Handlers ---

@dp.message(ReelsStates.waiting_for_description)
async def reels_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ReelsStates.waiting_for_psychotype)
    await message.answer("Выберите психотип аудитории:", reply_markup=get_reels_psycho_menu())

@dp.message(ReelsStates.waiting_for_psychotype)
async def reels_psychotype(message: types.Message, state: FSMContext):
    psycho_mapping = {
        "🧠 Убедить (Логик)": "логик",
        "💖 Вдохновить (Эмоционал)": "эмоционал",
        "⚡ Продать (Практик)": "практик",
        "🔥 В тренд (Социальщик)": "социальщик"
    }
    psychotype = psycho_mapping.get(message.text)
    if not psychotype:
        await message.answer("Пожалуйста, выберите один из вариантов на клавиатуре.")
        return

    await state.update_data(psychotype=psychotype)
    data = await state.get_data()
    
    await message.answer("Генерирую сценарий... ⏳", reply_markup=get_main_menu())
    await generate_reels(message, data["description"], data["psychotype"])
    await state.set_state(None)

async def generate_reels(message: types.Message, description: str, psychotype: str):
    system_prompt = prompts.REELS_SYSTEM_PROMPTS.get(psychotype, prompts.REELS_SYSTEM_PROMPTS["логик"])
    user_prompt = prompts.REELS_USER_PROMPT.format(work_description=description)
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        result_text = response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        await message.answer("Произошла ошибка при генерации сценария. Пожалуйста, попробуйте позже.")
        return

    await message.answer(result_text, reply_markup=get_retry_inline_keyboard("reels"))


# --- Inline Handlers for Retry ---

@dp.callback_query(F.data.startswith("retry_"))
async def callback_retry(callback: types.CallbackQuery, state: FSMContext):
    action_type = callback.data.split("_")[1]
    data = await state.get_data()
    
    # Hide the button on the old message to avoid duplicate clicks
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if action_type == "caption":
        if "design" in data and "shape" in data and "length" in data:
            await callback.message.answer("Генерирую подпись заново... ⏳")
            await generate_caption(callback.message, data["design"], data["shape"], data["length"])
        else:
            await callback.message.answer("Нет данных для повторной генерации. Пожалуйста, начните сначала.")
            
    elif action_type == "reels":
        if "description" in data and "psychotype" in data:
            await callback.message.answer("Генерирую сценарий заново... ⏳")
            await generate_reels(callback.message, data["description"], data["psychotype"])
        else:
            await callback.message.answer("Нет данных для повторной генерации. Пожалуйста, начните сначала.")
    
    await callback.answer()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
