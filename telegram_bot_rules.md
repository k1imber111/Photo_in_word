# Правила разработки Telegram-ботов на Python

> Источники: [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice),
> [cursor.directory](https://cursor.directory/), [python-telegram-bot docs](https://docs.python-telegram-bot.org),
> [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)

---

## 1. Стек и зависимости

```
python-telegram-bot>=21.0   # основная библиотека
python-dotenv               # переменные окружения
sqlalchemy>=2.0             # ORM для БД (если нужна)
alembic                     # миграции БД
redis                       # кэш и хранение сессий (для продакшена)
ruff                        # линтер
pytest                      # тесты
pytest-asyncio              # асинхронные тесты
```

**Установка:**
```bash
pip install python-telegram-bot[job-queue] python-dotenv sqlalchemy ruff pytest pytest-asyncio
```

---

## 2. Структура проекта

```
my_bot/
├── bot.py                  # точка входа, создание Application
├── config.py               # настройки через pydantic-settings или dataclass
├── .env                    # токены и секреты (в .gitignore!)
├── handlers/
│   ├── __init__.py
│   ├── commands.py         # /start, /help, /cancel
│   ├── messages.py         # обработка текстовых сообщений
│   ├── callbacks.py        # inline-кнопки (CallbackQueryHandler)
│   └── errors.py           # глобальный обработчик ошибок
├── services/
│   ├── __init__.py
│   └── database.py         # работа с БД
├── models/
│   ├── __init__.py
│   └── user.py             # модели данных
├── keyboards/
│   ├── __init__.py
│   └── inline.py           # фабрики клавиатур
├── utils/
│   ├── __init__.py
│   └── helpers.py          # вспомогательные функции
├── tests/
│   ├── __init__.py
│   └── test_handlers.py
├── requirements.txt
└── README.md
```

---

## 3. Архитектурные принципы

### 3.1 Application как основа

```python
from telegram.ext import Application, ApplicationBuilder

async def main() -> None:
    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .build()
    )
    app.add_handler(CommandHandler("start", start_handler))
    await app.run_polling()
```

Никогда не использовать прямые вызовы `Bot.get_updates()` — только через `Application`.

### 3.2 Разделение ответственности

- **handlers/** — только маршрутизация и минимальная логика
- **services/** — бизнес-логика, работа с БД и внешними API
- **keyboards/** — фабрики клавиатур, не создавать в handlers
- **models/** — структуры данных, Pydantic или dataclass

### 3.3 ConversationHandler для диалогов

```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

STEP_NAME, STEP_PHONE = range(2)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        STEP_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
```

### 3.4 Polling vs Webhook

| Режим | Когда использовать |
|-------|--------------------|
| Polling | Разработка, тестирование, малые боты |
| Webhook | Продакшен — ниже задержка, меньше нагрузка |

---

## 4. Безопасность

- **Никогда** не хранить токен в коде — только в `.env`
- `.env` всегда в `.gitignore`
- Проверять `update.effective_user.id` для admin-команд
- Не логировать токен и персональные данные пользователей
- Валидировать все входящие данные от пользователя

```python
# config.py — безопасная загрузка конфига
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.environ["BOT_TOKEN"]  # KeyError если не задан
    ADMIN_IDS: list[int] = None

    def __post_init__(self) -> None:
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = []

config = Config()
```

---

## 5. Стандарты кода

### 5.1 Типизация — обязательна

```python
from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}!")
```

### 5.2 Docstrings для всех публичных функций

```python
async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет главное меню пользователю.

    Args:
        update: Объект обновления Telegram.
        context: Контекст обработчика.
    """
    ...
```

### 5.3 Клавиатуры — только через фабрики

```python
# keyboards/inline.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    buttons = [
        [InlineKeyboardButton("Профиль", callback_data="profile")],
        [InlineKeyboardButton("Помощь", callback_data="help")],
    ]
    return InlineKeyboardMarkup(buttons)
```

### 5.4 Обработка ошибок

```python
# handlers/errors.py
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок — логирует и уведомляет администратора."""
    logger.error("Ошибка при обработке обновления:", exc_info=context.error)
    # опционально: уведомить ADMIN_ID
```

---

## 6. Форматирование сообщений

- Использовать `ParseMode.HTML` (предпочтительно) или `ParseMode.MARKDOWN_V2`
- Экранировать специальные символы при MARKDOWN_V2
- Не смешивать форматирование в одном сообщении

```python
await update.message.reply_text(
    "<b>Ваш заказ</b> принят!\n"
    f"Номер: <code>{order_id}</code>",
    parse_mode="HTML",
)
```

---

## 7. Работа с состоянием

### Для разработки — PicklePersistence

```python
from telegram.ext import PicklePersistence

persistence = PicklePersistence(filepath="bot_data.pkl")
app = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
```

### Для продакшена — Redis или PostgreSQL

```python
# context.user_data сохраняется автоматически через persistence
context.user_data["step"] = "confirmed"
```

---

## 8. Планировщик задач (JobQueue)

```python
async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Плановое уведомление пользователям."""
    await context.bot.send_message(chat_id=context.job.chat_id, text="Напоминание!")

# При регистрации хендлера:
context.job_queue.run_repeating(send_reminder, interval=3600, chat_id=user_id)
```

---

## 9. Логирование

```python
import logging

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
```

- Уровень `INFO` в продакшене, `DEBUG` при разработке
- Не логировать токены, пароли, персональные данные

---

## 10. Тесты

```python
# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from handlers.commands import start_handler

@pytest.mark.asyncio
async def test_start_handler_replies() -> None:
    """Проверяет, что /start отправляет ответное сообщение."""
    update = MagicMock()
    update.effective_user.first_name = "Иван"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await start_handler(update, context)

    update.message.reply_text.assert_called_once()
```

Запуск тестов:
```bash
pytest tests/ -v --asyncio-mode=auto
```

---

## 11. Деплой

### Systemd (Linux)

```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/bot.py
Restart=always
EnvironmentFile=/path/to/.env

[Install]
WantedBy=multi-user.target
```

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

---

## 12. Чеклист перед запуском в продакшен

- [ ] Токен в `.env`, `.env` в `.gitignore`
- [ ] Глобальный `error_handler` зарегистрирован
- [ ] Команда `/cancel` работает в ConversationHandler
- [ ] Логирование настроено и протестировано
- [ ] Все admin-команды защищены проверкой `user_id`
- [ ] Сообщения не превышают лимит Telegram (4096 символов)
- [ ] Polling заменён на Webhook (для продакшена)
- [ ] Тесты проходят: `pytest tests/ -v`
- [ ] Линтер не выдаёт ошибок: `ruff check .`
