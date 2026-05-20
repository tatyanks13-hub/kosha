import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- Настройки ---
API_TOKEN = '' # Замени на свой токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Состояния ---
class Quiz(StatesGroup):
    q_index = State()
    scores = State()

# --- Вопросы теста (теперь их 10 для точности) ---
QUESTIONS = [
    {"text": "Как ощущается кожа через 20 минут после умывания водой?", "variants": {"А": "Сильно стянута", "Б": "Комфортно", "В": "Стянута только на щеках", "Г": "Местами уже блестит"}},
    {"text": "Как выглядит лицо в середине дня?", "variants": {"А": "Шелушится", "Б": "Матовое", "В": "Блестит Т-зона", "Г": "Сильно лоснится"}},
    {"text": "Твои поры в зеркале:", "variants": {"А": "Невидимы", "Б": "Едва заметны", "В": "Видны только на носу", "Г": "Расширены везде"}},
    {"text": "Часто ли бывают прыщи?", "variants": {"А": "Никогда", "Б": "Очень редко", "В": "Только в Т-зоне", "Г": "Часто по всему лицу"}},
    {"text": "Реакция на жирный крем:", "variants": {"А": "Приятно впитывается", "Б": "Нормально", "В": "Тяжело для лба", "Г": "Очень плохо, липко"}},
    {"text": "Цвет лица обычно:", "variants": {"А": "Тусклый, бледный", "Б": "Ровный, здоровый", "В": "Неоднородный", "Г": "Землистый или серый"}},
    {"text": "Кожа на ощупь часто:", "variants": {"А": "Шершавая", "Б": "Гладкая", "В": "Гладкая на лбу", "Г": "Скользкая"}},
    {"text": "Как держится макияж?", "variants": {"А": "Скатывается в чешуйки", "Б": "Хорошо весь день", "В": "Плывет на носу", "Г": "Исчезает через 2 часа"}},
    {"text": "Реакция на холод:", "variants": {"А": "Сильное покраснение", "Б": "Легкий румянец", "В": "Обветриваются щеки", "Г": "Почти нет реакции"}},
    {"text": "Тональный крем подчеркивает морщинки?", "variants": {"А": "Да, сильно", "Б": "Нет", "В": "Только под глазами", "Г": "Нет, он в них забивается"}}
]

# --- Результаты и рекомендации ---
ADVICE = {
    "А": {
        "type": "СУХАЯ",
        "desc": "Твоей коже не хватает жиров (себума).",
        "tips": "✅ Рекомендации:\n1. Используй мягкое молочко для умывания.\n2. Ищи в составе кремов масла (ши, жожоба) и сквалан.\n3. Пей больше воды и не забывай про ночной питательный крем."
    },
    "Б": {
        "type": "НОРМАЛЬНАЯ",
        "desc": "Идеальный баланс воды и жира.",
        "tips": "✅ Рекомендации:\n1. Твоя цель — сохранить то, что есть.\n2. Используй легкие увлажняющие эмульсии.\n3. Обязательно защищай кожу SPF-кремом летом."
    },
    "В": {
        "type": "КОМБИНИРОВАННАЯ",
        "desc": "Жирная Т-зона и нормальные или сухие щеки.",
        "tips": "✅ Рекомендации:\n1. Используй мультимаскинг: очищающие маски на нос, увлажняющие — на щеки.\n2. Выбирай гелевые текстуры кремов.\n3. Используй тоники без спирта."
    },
    "Г": {
        "type": "ЖИРНАЯ",
        "desc": "Сальные железы работают слишком активно.",
        "tips": "✅ Рекомендации:\n1. Не пересушивай кожу спиртом (это вызовет еще больше жира!).\n2. Используй средства с салициловой кислотой и ниацинамидом.\n3. Выбирай безмасляные (oil-free) увлажняющие средства."
    }
}

# --- Логика ---

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardBuilder()
    kb.button(text="🚀 Начать тест")
    await message.answer("Привет! Давай узнаем твой тип кожи и подберем уход. Нажми на кнопку ниже 👇", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text.in_(["🚀 Начать тест", "🔄 Пройти заново"]))
async def start_quiz(message: types.Message, state: FSMContext):
    await state.update_data(q_index=0, scores={"А": 0, "Б": 0, "В": 0, "Г": 0})
    await state.set_state(Quiz.q_index)
    await ask_question(message, 0)

async def ask_question(message: types.Message, q_idx: int):
    question = QUESTIONS[q_idx]
    kb = ReplyKeyboardBuilder()
    # Сортируем кнопки по порядку
    for key in sorted(question["variants"].keys()):
        kb.button(text=f"{key}) {question['variants'][key]}")
    kb.adjust(1)
    await message.answer(f"Вопрос {q_idx + 1}/{len(QUESTIONS)}:\n\n{question['text']}",
                         reply_markup=kb.as_markup(resize_keyboard=True))


@dp.message(Quiz.q_index)
async def handle_answer(message: types.Message, state: FSMContext):
    # Проверка на корректность ввода
    if not message.text or message.text[0].upper() not in ["А", "Б", "В", "Г"]:
        await message.answer("Пожалуйста, выбери вариант кнопкой на клавиатуре!")
        return

    data = await state.get_data()
    q_idx = data['q_index']
    scores = data['scores']

    user_choice = message.text[0].upper()
    scores[user_choice] += 1
    new_q_idx = q_idx + 1

    if new_q_idx < len(QUESTIONS):
        await state.update_data(q_index=new_q_idx, scores=scores)
        await ask_question(message, new_q_idx)
    else:
        # Итог
        final_type = max(scores, key=scores.get)
        result = ADVICE[final_type]

        finish_text = (
            f"🏆 **Результат: {result['type']} КОЖА**\n\n"
            f"{result['desc']}\n\n"
            f"{result['tips']}"
        )

        kb = ReplyKeyboardBuilder()
        kb.button(text="🔄 Пройти заново")

        await message.answer(finish_text, parse_mode="Markdown", reply_markup=kb.as_markup(resize_keyboard=True))
        await state.clear()


async def main():
    print("Бот запущен и ждет сообщений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
