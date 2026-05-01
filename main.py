import telebot
import psutil
import os
import subprocess
import time
import ctypes
import platform
from datetime import datetime
from PIL import ImageGrab
import io

# ========== ПЕРЕМЕННЫЕ ИЗ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ТВОЙ_ТОКЕН_СЮДА")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))  # Telegram ID (число)
# =============================================

# Проверка, что токен и ID заданы
if BOT_TOKEN == "ТВОЙ_ТОКЕН_СЮДА" or ADMIN_ID == 0:
    print("ОШИБКА: Задай BOT_TOKEN и ADMIN_ID в переменных окружения Railway")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(message):
    return message.chat.id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message):
        bot.reply_to(message, "❌ Доступ запрещён")
        return
    bot.reply_to(message,
        "✅ Бот запущен на Railway!\n\n"
        "📸 /screenshot — скриншот (серверный рабочий стол? нет, вернёт заглушку)\n"
        "⚠️ На Railway нет графического интерфейса, скриншот будет чёрным.\n"
        "🔌 /shutdown — выключить ПК (работает только если бот на твоём ПК)\n"
        "💻 /run [команда] — выполнить команду на сервере\n"
        "📂 /get [путь] — скачать файл с сервера\n"
        "📋 /ps — процессы сервера\n"
        "🖥️ /info — информация о сервере")

# Скриншот (заглушка — сервер без GUI)
@bot.message_handler(commands=['screenshot'])
def screenshot(message):
    if not is_admin(message):
        return
    try:
        # Пытаемся сделать скриншот (на сервере будет чёрный экран)
        img = ImageGrab.grab()
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        bot.send_photo(ADMIN_ID, img_bytes, caption="📸 Скриншот (на Railway будет пустым)")
    except Exception as e:
        bot.reply_to(message, f"❌ Скриншот недоступен на сервере без GUI: {e}")

# Выключение (не работает на Railway, но можно удалить команду)
@bot.message_handler(commands=['shutdown'])
def shutdown(message):
    if not is_admin(message):
        return
    bot.reply_to(message, "❌ Выключение недоступно на Railway. Эта команда работает только на твоём ПК.")

# Перезагрузка (тоже не работает)
@bot.message_handler(commands=['restart'])
def restart(message):
    if not is_admin(message):
        return
    bot.reply_to(message, "❌ Перезагрузка недоступна на Railway.")

@bot.message_handler(commands=['run'])
def run_command(message):
    if not is_admin(message):
        return
    cmd = message.text.replace('/run', '', 1).strip()
    if not cmd:
        bot.reply_to(message, "❌ Введите команду: /run ls -la")
        return
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n...[обрезано]"
        if not output.strip():
            output = "[команда выполнена без вывода]"
        bot.reply_to(message, f"💻 `{cmd}`\n\n```\n{output}\n```", parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "⏰ Команда выполнялась слишком долго")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['get'])
def get_file(message):
    if not is_admin(message):
        return
    path = message.text.replace('/get', '', 1).strip()
    if not path or not os.path.exists(path):
        bot.reply_to(message, f"❌ Файл не найден: {path}")
        return
    try:
        with open(path, 'rb') as f:
            bot.send_document(ADMIN_ID, f, caption=f"📁 {os.path.basename(path)}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['ps'])
def process_list(message):
    if not is_admin(message):
        return
    processes = ""
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            processes += f"{proc.info['pid']}: {proc.info['name']} [{proc.info['memory_percent']:.1f}%]\n"
        except:
            pass
        if len(processes) > 3900:
            processes += "..."
            break
    if not processes:
        processes = "Не удалось получить список процессов"
    if len(processes) > 4000:
        processes = processes[:4000]
    bot.reply_to(message, f"📋 **Процессы:**\n```\n{processes}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def sysinfo(message):
    if not is_admin(message):
        return
    info = f"""
🖥️ **Системная информация (Railway)**
━━━━━━━━━━━━━━━━━━━━━━━━
💻 **OS**: {platform.system()} {platform.release()}
🏷️ **Hostname**: {platform.node()}
🐍 **Python**: {platform.python_version()}
📊 **CPU**: {psutil.cpu_percent()}%
🧠 **RAM**: {psutil.virtual_memory().percent}%
💾 **Disk**: {psutil.disk_usage('/').percent}%
    """
    bot.reply_to(message, info, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo(message):
    if is_admin(message):
        bot.reply_to(message, "❓ Неизвестная команда. Напиши /start")

if __name__ == "__main__":
    print("🚀 Бот запущен на Railway!")
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
