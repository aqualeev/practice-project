import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import requests

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# НАСТРОЙКА ПРОКСИ (замените на ваши данные)
# Если у вас нет прокси, пропустите этот блок
PROXY_HOST = None  # Например: "45.67.34.21"
PROXY_PORT = None   # Например: 8080
PROXY_USER = None   # Если нужна аутентификация
PROXY_PASS = None   # Если нужна аутентификация

# Создаем прокси словарь для requests (для API погоды)
proxies = {}
if PROXY_HOST and PROXY_PORT:
    proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
    if PROXY_USER and PROXY_PASS:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

# Настройка прокси для TeleBot
if PROXY_HOST and PROXY_PORT:
    from telebot import apihelper
    proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
    if PROXY_USER and PROXY_PASS:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    apihelper.proxy = {'https': proxy_url}

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

def get_weather_by_coords(lat, lon):
    """Получает погоду по координатам"""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    try:
        # Используем прокси если они заданы
        if proxies:
            response = requests.get(url, timeout=10, proxies=proxies)
        else:
            response = requests.get(url, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            return format_weather_data(data)
        else:
            print(f"Ошибка API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def get_weather_by_city(city):
    """Получает погоду по названию города"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    try:
        # Используем прокси если они заданы
        if proxies:
            response = requests.get(url, timeout=10, proxies=proxies)
        else:
            response = requests.get(url, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            return format_weather_data(data)
        else:
            return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def format_weather_data(data):
    """Форматирует данные о погоде"""
    weather_emoji = {
        "clear": "☀️",
        "clouds": "☁️",
        "rain": "🌧",
        "drizzle": "🌦",
        "thunderstorm": "⛈",
        "snow": "❄️",
        "mist": "🌫",
        "smoke": "💨",
        "haze": "🌫",
        "fog": "🌫"
    }
    
    description = data["weather"][0]["description"].lower()
    emoji = "🌡"
    for key, value in weather_emoji.items():
        if key in description:
            emoji = value
            break
    
    temp = data["main"]["temp"]
    temp_emoji = "🔥" if temp > 25 else "❄️" if temp < 0 else "🌡"
    
    message = (
        f"{emoji} *Погода в {data['name']}, {data.get('sys', {}).get('country', '')}* {temp_emoji}\n\n"
        f"🌡 Температура: *{temp:.1f}°C*\n"
        f"🤔 Ощущается как: *{data['main']['feels_like']:.1f}°C*\n"
        f"💧 Влажность: *{data['main']['humidity']}%*\n"
        f"💨 Ветер: *{data['wind']['speed']:.1f} м/с*\n"
        f"📊 Давление: *{data['main']['pressure']} гПа*\n"
        f"📝 {data['weather'][0]['description'].capitalize()}"
    )
    
    return message

def get_main_keyboard():
    """Создает клавиатуру"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_location = KeyboardButton("📍 Отправить геолокацию", request_location=True)
    btn_help = KeyboardButton("ℹ️ Помощь")
    keyboard.add(btn_location, btn_help)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"🌍 *Привет, {user_name}!*\n\n"
        "Я бот погоды 🤖\n\n"
        "📱 *Что я умею:*\n"
        "• Показывать погоду по геолокации\n"
        "• Искать погоду в любом городе мира\n\n"
        "👇 *Попробуй прямо сейчас:*\n"
        "• Нажми кнопку '📍 Отправить геолокацию'\n"
        "• Или просто напиши название города"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 *Справка*\n\n"
        "*Как получить погоду:*\n\n"
        "1️⃣ *По геолокации*\n"
        "   Нажми кнопку '📍 Отправить геолокацию'\n"
        "   Разреши доступ к местоположению\n\n"
        "2️⃣ *По названию города*\n"
        "   Просто напиши название города в чат\n"
        "   Например: Москва, London, Tokyo\n\n"
        "*Советы:*\n"
        "• Можно писать на русском или английском\n"
        "• Если город не найден - проверь написание"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['weather'])
def cmd_weather(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши город после команды.\nПример: `/weather Москва`", parse_mode='Markdown')
        return
    
    city = args[1].strip()
    msg = bot.send_message(message.chat.id, "🔍 Ищу погоду...")
    
    weather = get_weather_by_city(city)
    if weather:
        bot.edit_message_text(weather, message.chat.id, msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(
            f"❌ Город *{city}* не найден.\n\nПопробуй написать на английском.",
            message.chat.id,
            msg.message_id,
            parse_mode='Markdown'
        )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    
    msg = bot.send_message(message.chat.id, "📍 Получаю погоду по вашему местоположению...")
    
    weather = get_weather_by_coords(lat, lon)
    if weather:
        bot.edit_message_text(weather, message.chat.id, msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(
            "❌ Не удалось получить погоду.\nПопробуй позже.",
            message.chat.id,
            msg.message_id
        )

@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def handle_help_button(message):
    send_help(message)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Игнорируем команды
    if message.text.startswith('/'):
        return
    
    city = message.text.strip()
    
    # Игнорируем слишком короткие сообщения
    if len(city) < 2:
        return
    
    msg = bot.send_message(message.chat.id, "🔍 Ищу город...")
    
    weather = get_weather_by_city(city)
    if weather:
        bot.edit_message_text(weather, message.chat.id, msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(
            f"❌ Город *{city}* не найден.\n\n💡 Попробуй:\n• Проверить написание\n• Нажать кнопку геолокации",
            message.chat.id,
            msg.message_id,
            parse_mode='Markdown'
        )

# Запуск бота
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 WeatherBot запущен!")
    print("📡 Бот готов к работе")
    print("=" * 50)
    
    # Проверяем подключение к Telegram API
    try:
        # Пытаемся получить информацию о боте
        bot.get_me()
        print("✅ Подключение к Telegram API установлено!")
    except Exception as e:
        print(f"⚠️ Ошибка подключения: {e}")
        print("💡 Возможно, нужен VPN или прокси")
    
    try:
        # Убираем вебхук и запускаем polling
        bot.remove_webhook()
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
