You are an expert Python developer specializing in Telegram bots.

Build a simple, clean Telegram bot for a nail salon content generator.

## Tech Stack
- Python 3.11+
- aiogram 3.x (Telegram Bot API)
- OpenAI API (gpt-5.4-mini) 
- python-dotenv for config
- NO database needed

## Project Structure
nail-bot/
├── bot.py                  # Entry point + all handlers
├── config.py               # Settings from .env
├── prompts.py              # All GPT prompts
├── .env.example
└── requirements.txt

## Core Features

### Feature 1: Photo Caption Generator
User flow:
1. Taps "📸 Подпись к фото" button
2. Bot asks: design type (nude/bright/french/art)
3. Bot asks: nail shape (almond/square/oval/coffin)
4. Bot asks: nail length (short/medium/long)
5. Bot generates caption with hashtags for Kazakhstan/Russia market

### Feature 2: Reels Script Generator
User flow:
1. Taps "🎬 Сценарий Reels" button
2. Bot asks: describe the work (free text input)
3. Bot shows 4 psychotype buttons:
   - 🧠 Убедить (Логик) — facts, technique, quality proof
   - 💖 Вдохновить (Эмоционал) — beauty, atmosphere, feelings
   - ⚡ Продать (Практик) — price, speed, practical result
   - 🔥 В тренд (Социальщик) — trends, social proof, FOMO
4. Bot generates a Reels script (hook 0-2s, body 3-20s, CTA 18-20s)
   tailored to selected psychotype

## OpenAI Prompts (implement in prompts.py)

### Caption Prompt
System: "Ты — профессиональный SMM-копирайтер для ногтевых салонов.
Пиши живые, продающие подписи к фото работ мастера маникюра."

User: "Напиши подпись к фото маникюра.
Дизайн: {design}. Форма: {shape}. Длина: {length}.
Структура: 1-2 предложения описания → краткий призыв к записи →
5-7 хэштегов (микс популярных и гео).
Длина: 600-900 символов."

### Reels Prompts (4 psychotypes, implement all in prompts.py)

ЛОГИК:
System: "Ты пишешь сценарии Reels для мастеров маникюра.
Аудитория: аналитики, которые изучают перед покупкой.
Структура: хук с фактом/вопросом → объяснение техники/качества → CTA с конкретикой."

ЭМОЦИОНАЛ:
System: "Ты пишешь сценарии Reels для мастеров маникюра.
Аудитория: люди, которые покупают на эмоциях и красоте.
Структура: визуальный хук с атмосферой → эстетичный процесс → мягкий CTA."

ПРАКТИК:
System: "Ты пишешь сценарии Reels для мастеров маникюра.
Аудитория: занятые люди, которым важны цена, скорость, результат.
Структура: хук с выгодой → быстрый результат до/после → CTA с ценой/датами."

СОЦИАЛЬЩИК:
System: "Ты пишешь сценарии Reels для мастеров маникюра.
Аудитория: люди, ориентированные на тренды и социальное доказательство.
Структура: хук 'все делают это' → тренд + примеры → CTA с дефицитом."

Reels user prompt (same for all 4):
"Тема видео: {work_description}.
Напиши сценарий с таймкодами:
[0-2 сек] Хук
[3-20 сек] Основная часть (3 коротких тезиса или действия)
[18-20 сек] CTA
Пиши конкретно, как будто мастер читает по бумажке перед камерой."

## Important Requirements
- All bot messages in Russian
- Use FSM (Finite State Machine) via aiogram for multi-step dialogs
- Async throughout (async/await everywhere)
- Error handling: if OpenAI fails → friendly Russian error message
- .env.example with BOT_TOKEN and OPENAI_API_KEY placeholders
- requirements.txt with pinned versions
- Add inline "🔄 Сгенерировать ещё раз" button after every generation
- Main menu always accessible via /menu command
- Keep the code simple and readable — no overengineering