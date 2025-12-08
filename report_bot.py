import os
import telebot
from telebot import types
from datetime import datetime


TOKEN = os.getenv("TOKEN")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")

if MANAGER_CHAT_ID is not None:
    try:
        MANAGER_CHAT_ID = int(MANAGER_CHAT_ID)
    except ValueError:
        print("⚠ Ошибка: MANAGER_CHAT_ID в переменных окружения не число.")
        MANAGER_CHAT_ID = None

if not TOKEN:
    raise RuntimeError("❌ Не задан TOKEN в переменных окружения!")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Шаги "машины состояний"
STEP_DATE = 1
STEP_VITRINA = 2
STEP_EDUCATION = 3
STEP_TASKS = 4
STEP_COACHING = 5
STEP_COMPLAINTS = 6
STEP_EXTRA = 7

user_state = {}
user_report = {}


def init_report(user_id: int):
    """Создаём пустую структуру отчёта для пользователя."""
    user_report[user_id] = {
        "date": "",
        "vitrina": "",
        "education": "",
        "tasks": "",
        "coaching": "",
        "complaints": "",
        "extra": "",
    }


def main_keyboard():
    """Главная клавиатура с кнопками."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Отправить отчёт", "Перезапустить")
    return kb


def ask_date(chat_id: int):
    """Спрашиваем дату отчёта."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Сегодня", "Ввести дату вручную")
    bot.send_message(
        chat_id,
        (
            "🗓 Укажи дату, за которую делается отчёт.\n\n"
            "Можешь нажать «Сегодня» или ввести дату вручную."
        ),
        reply_markup=kb,
    )


@bot.message_handler(commands=["start"])
def start(message):
    """Стартовая команда."""
    chat_id = message.chat.id
    text = (
        "Привет! Я бот для ежедневных отчётов менеджера студии.\n\n"
        "Используй кнопки внизу:\n"
        "• «Отправить отчёт» — чтобы заполнить отчёт за смену\n"
        "• «Перезапустить» — чтобы начать заполнение заново"
    )
    bot.send_message(chat_id, text, reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text == "Отправить отчёт")
def button_send_report(message):
    """Начинаем новый отчёт по кнопке."""
    user_id = message.from_user.id
    init_report(user_id)
    user_state[user_id] = STEP_DATE
    ask_date(message.chat.id)


@bot.message_handler(func=lambda m: m.text == "Перезапустить")
def button_restart(message):
    """Сбрасываем текущее состояние и начинаем отчёт заново."""
    user_id = message.from_user.id
    user_state.pop(user_id, None)
    user_report.pop(user_id, None)

    bot.send_message(
        message.chat.id,
        "Начинаем отчёт заново 🌀",
        reply_markup=main_keyboard(),
    )

    init_report(user_id)
    user_state[user_id] = STEP_DATE
    ask_date(message.chat.id)


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_DATE)
def handle_date(message):
    """Обрабатываем дату отчёта."""
    user_id = message.from_user.id
    text = message.text.strip()

    if text.lower() == "сегодня":
        date_str = datetime.now().strftime("%d.%m.%Y")
    elif text.lower().startswith("ввести дату"):
        bot.send_message(
            message.chat.id,
            "Напиши дату в формате ДД.ММ.ГГГГ (например, 08.12.2025).",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        return
    else:
        try:
            datetime.strptime(text, "%d.%m.%Y")
            date_str = text
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Не понял дату 🙈 Напиши в формате ДД.ММ.ГГГГ (например, 08.12.2025).",
            )
            return

    user_report[user_id]["date"] = date_str
    user_state[user_id] = STEP_VITRINA

    bot.send_message(
        message.chat.id,
        (
            "1️⃣ <b>Витрина</b>\n"
            "С кем работали по витрине: ID, что писали, похвала, рекомендации."
        ),
        reply_markup=types.ReplyKeyboardRemove(),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_VITRINA)
def handle_vitrina(message):
    """Блок по витрине."""
    user_id = message.from_user.id
    user_report[user_id]["vitrina"] = message.text.strip()
    user_state[user_id] = STEP_EDUCATION

    bot.send_message(
        message.chat.id,
        (
            "2️⃣ <b>Обучения</b>\n"
            "Сколько обучений, формат (звонок/видео), ID и итог "
            "(перспективная / средняя / низкая мотивация)."
        ),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_EDUCATION)
def handle_education(message):
    """Блок по обучениям."""
    user_id = message.from_user.id
    user_report[user_id]["education"] = message.text.strip()
    user_state[user_id] = STEP_TASKS

    bot.send_message(
        message.chat.id,
        (
            "3️⃣ <b>Таск-трекер</b>\n"
            "Статус задач (обработан / частично / не выполнен) и важные моменты."
        ),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_TASKS)
def handle_tasks(message):
    """Блок по таск-трекеру."""
    user_id = message.from_user.id
    user_report[user_id]["tasks"] = message.text.strip()
    user_state[user_id] = STEP_COACHING

    bot.send_message(
        message.chat.id,
        (
            "4️⃣ <b>Таблица коучинга</b>\n"
            "По кому были апдейты: ID, цель (урок, ДЗ, пуш, звонок, график) и итог."
        ),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_COACHING)
def handle_coaching(message):
    """Блок по коучингу."""
    user_id = message.from_user.id
    user_report[user_id]["coaching"] = message.text.strip()
    user_state[user_id] = STEP_COMPLAINTS

    bot.send_message(
        message.chat.id,
        (
            "5️⃣ <b>Жалобы моделей</b>\n"
            "Если были: ID, суть жалобы, что сделали."
        ),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_COMPLAINTS)
def handle_complaints(message):
    """Блок по жалобам."""
    user_id = message.from_user.id
    user_report[user_id]["complaints"] = message.text.strip()
    user_state[user_id] = STEP_EXTRA

    bot.send_message(
        message.chat.id,
        (
            "6️⃣ <b>Дополнительно</b>\n"
            "Любые важные моменты за день: проблемы, предложения, модели на контроле."
        ),
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == STEP_EXTRA)
def handle_extra(message):
    """Финальный блок — доп.инфо, сбор и отправка отчёта."""
    user_id = message.from_user.id
    user_report[user_id]["extra"] = message.text.strip()

    rep = user_report[user_id]
    text = (
        "📅 <b>Ежедневный отчёт менеджера</b>\n"
        f"Дата: <b>{rep['date']}</b>\n\n"
        f"1️⃣ <b>Витрина</b>\n{rep['vitrina']}\n\n"
        f"2️⃣ <b>Обучения</b>\n{rep['education']}\n\n"
        f"3️⃣ <b>Таск-трекер</b>\n{rep['tasks']}\n\n"
        f"4️⃣ <b>Таблица коучинга</b>\n{rep['coaching']}\n\n"
        f"5️⃣ <b>Жалобы моделей</b>\n{rep['complaints']}\n\n"
        f"6️⃣ <b>Дополнительно</b>\n{rep['extra']}"
    )

    # Отправляем отчёт самому менеджеру
    bot.send_message(
        user_id,
        "✅ Отчёт сформирован, вот он:",
    )
    bot.send_message(
        user_id,
        text,
        reply_markup=main_keyboard(),
    )

    # Дублируем отчёт в общий менеджерский чат, если указан
    if MANAGER_CHAT_ID is not None:
        bot.send_message(MANAGER_CHAT_ID, text)

    # Чистим состояние
    user_state.pop(user_id, None)
    user_report.pop(user_id, None)


if __name__ == "__main__":
    print("Бот запущен на Railway (или локально). Нажми Ctrl+C, чтобы остановить локально.")
    # На всякий случай задаём таймауты, чтобы бот лучше переживал обрывы соединения
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
