import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

bot = telebot.TeleBot(TOKEN)

# Создание базы данных
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'ru',
            subscribed INTEGER DEFAULT 0,
            join_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cheats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            version TEXT,
            description TEXT,
            download_link TEXT,
            screenshot_id TEXT,
            instructions TEXT,
            added_date TEXT,
            added_by INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_username TEXT,
            channel_link TEXT,
            added_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_language_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    btn_en = types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    btn_ua = types.InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua")
    markup.add(btn_ru, btn_en, btn_ua)
    return markup

def get_main_menu_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    lang = result[0] if result else 'ru'
    
    if lang == 'ru':
        btn_cheats = types.KeyboardButton("📋 Список читов")
        btn_settings = types.KeyboardButton("⚙️ Настройки")
    elif lang == 'en':
        btn_cheats = types.KeyboardButton("📋 Cheats List")
        btn_settings = types.KeyboardButton("⚙️ Settings")
    else:
        btn_cheats = types.KeyboardButton("📋 Список читів")
        btn_settings = types.KeyboardButton("⚙️ Налаштування")
    
    markup.add(btn_cheats, btn_settings)
    return markup

def get_versions_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    versions = [
        ("1.8.8", "ver_1.8.8"),
        ("1.12.2", "ver_1.12.2"),
        ("1.16.5", "ver_1.16.5"),
        ("1.21+", "ver_1.21+")
    ]
    
    for version_name, callback in versions:
        btn = types.InlineKeyboardButton(f"🎮 {version_name}", callback_data=callback)
        markup.add(btn)
    
    return markup

def get_settings_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    lang = result[0] if result else 'ru'
    
    if lang == 'ru':
        btn_change_lang = types.InlineKeyboardButton("🌐 Сменить язык", callback_data="change_lang")
        btn_channel = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/your_channel")
    elif lang == 'en':
        btn_change_lang = types.InlineKeyboardButton("🌐 Change Language", callback_data="change_lang")
        btn_channel = types.InlineKeyboardButton("📢 Our Channel", url="https://t.me/your_channel")
    else:
        btn_change_lang = types.InlineKeyboardButton("🌐 Змінити мову", callback_data="change_lang")
        btn_channel = types.InlineKeyboardButton("📢 Наш канал", url="https://t.me/your_channel")
    
    markup.add(btn_change_lang, btn_channel)
    return markup

def check_subscription(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_username FROM channels')
    channels = cursor.fetchall()
    conn.close()
    
    if not channels:
        return True
    
    for channel in channels:
        try:
            member = bot.get_chat_member(f"@{channel[0]}", user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            continue
    
    return True

def get_subscription_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_username, channel_link FROM channels')
    channels = cursor.fetchall()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    lang_result = cursor.fetchone()
    conn.close()
    
    lang = lang_result[0] if lang_result else 'ru'
    
    for channel in channels:
        btn = types.InlineKeyboardButton(f"📢 Подписаться на {channel[0]}", url=channel[1])
        markup.add(btn)
    
    if lang == 'ru':
        btn_check = types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")
    elif lang == 'en':
        btn_check = types.InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")
    else:
        btn_check = types.InlineKeyboardButton("✅ Перевірити підписку", callback_data="check_sub")
    
    markup.add(btn_check)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)',
                      (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    
    conn.close()
    
    bot.send_message(
        user_id,
        "🇷🇺 Выберите язык / 🇬🇧 Choose language / 🇺🇦 Виберіть мову:",
        reply_markup=get_language_keyboard()
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "⛔ У вас нет доступа к админ-панели!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add_cheat = types.InlineKeyboardButton("📝 Добавить чит", callback_data="admin_add_cheat")
    btn_add_channel = types.InlineKeyboardButton("📢 Добавить канал", callback_data="admin_add_channel")
    btn_list_cheats = types.InlineKeyboardButton("📋 Список читов", callback_data="admin_list_cheats")
    btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    
    markup.add(btn_add_cheat, btn_add_channel)
    markup.add(btn_list_cheats, btn_stats)
    
    bot.send_message(user_id, "🔐 Админ-панель:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id
    data = call.data
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    lang = result[0] if result else 'ru'
    conn.close()
    
    if data.startswith('lang_'):
        selected_lang = data.split('_')[1]
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (selected_lang, user_id))
        conn.commit()
        conn.close()
        
        if not check_subscription(user_id):
            if selected_lang == 'ru':
                msg = "📢 Для использования бота подпишитесь на канал:"
            elif selected_lang == 'en':
                msg = "📢 To use the bot, subscribe to the channel:"
            else:
                msg = "📢 Для використання бота підпишіться на канал:"
            
            bot.edit_message_text(msg, user_id, call.message.message_id, reply_markup=get_subscription_markup(user_id))
        else:
            if selected_lang == 'ru':
                msg = "✅ Язык установлен: Русский\nИспользуйте меню для навигации:"
            elif selected_lang == 'en':
                msg = "✅ Language set: English\nUse the menu to navigate:"
            else:
                msg = "✅ Мову встановлено: Українська\nВикористовуйте меню для навігації:"
            
            bot.edit_message_text(msg, user_id, call.message.message_id)
            bot.send_message(user_id, "👇 Меню:", reply_markup=get_main_menu_keyboard(user_id))
    
    elif data == 'check_sub':
        if check_subscription(user_id):
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET subscribed = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            lang = cursor.fetchone()[0]
            conn.close()
            
            if lang == 'ru':
                msg = "✅ Подписка подтверждена! Добро пожаловать!"
            elif lang == 'en':
                msg = "✅ Subscription confirmed! Welcome!"
            else:
                msg = "✅ Підписку підтверджено! Ласкаво просимо!"
            
            bot.edit_message_text(msg, user_id, call.message.message_id)
            bot.send_message(user_id, "👇 Меню:", reply_markup=get_main_menu_keyboard(user_id))
        else:
            if lang == 'ru':
                msg = "❌ Вы не подписались на все каналы!"
            elif lang == 'en':
                msg = "❌ You haven't subscribed to all channels!"
            else:
                msg = "❌ Ви не підписалися на всі канали!"
            
            bot.answer_callback_query(call.id, msg, show_alert=True)
    
    elif data.startswith('ver_'):
        version = data.replace('ver_', '')
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, description, download_link, instructions FROM cheats WHERE version = ?', (version,))
        cheats = cursor.fetchall()
        conn.close()
        
        if cheats:
            for cheat in cheats:
                if lang == 'ru':
                    msg = f"🎮 *{cheat[0]}*\n\n📋 Версия: {version}\n📝 Описание: {cheat[1]}\n\n📥 Скачать: {cheat[2]}\n\n📖 Инструкция: {cheat[3]}"
                elif lang == 'en':
                    msg = f"🎮 *{cheat[0]}*\n\n📋 Version: {version}\n📝 Description: {cheat[1]}\n\n📥 Download: {cheat[2]}\n\n📖 Instructions: {cheat[3]}"
                else:
                    msg = f"🎮 *{cheat[0]}*\n\n📋 Версія: {version}\n📝 Опис: {cheat[1]}\n\n📥 Завантажити: {cheat[2]}\n\n📖 Інструкція: {cheat[3]}"
                
                bot.send_message(user_id, msg, parse_mode="Markdown")
        else:
            if lang == 'ru':
                msg = "❌ Нет доступных читов для этой версии"
            elif lang == 'en':
                msg = "❌ No cheats available for this version"
            else:
                msg = "❌ Немає доступних читів для цієї версії"
            
            bot.send_message(user_id, msg)
    
    elif data == 'change_lang':
        bot.edit_message_text(
            "🇷🇺 Выберите язык / 🇬🇧 Choose language / 🇺🇦 Виберіть мову:",
            user_id,
            call.message.message_id,
            reply_markup=get_language_keyboard()
        )
    
    elif data == 'admin_add_cheat':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Нет доступа!")
            return
        
        msg = bot.send_message(user_id, "Введите данные чита в формате:\n\nНазвание\nВерсия (1.8.8/1.12.2/1.16.5/1.21+)\nОписание\nСсылка для скачивания\nИнструкция")
        bot.register_next_step_handler(msg, process_add_cheat)
    
    elif data == 'admin_add_channel':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Нет доступа!")
            return
        
        msg = bot.send_message(user_id, "Введите username канала (без @) и ссылку на канал через пробел:")
        bot.register_next_step_handler(msg, process_add_channel)
    
    elif data == 'admin_list_cheats':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Нет доступа!")
            return
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, version FROM cheats')
        cheats = cursor.fetchall()
        conn.close()
        
        if cheats:
            markup = types.InlineKeyboardMarkup()
            for cheat in cheats:
                btn = types.InlineKeyboardButton(f"🗑 {cheat[1]} ({cheat[2]})", callback_data=f"admin_delete_cheat_{cheat[0]}")
                markup.add(btn)
            
            bot.edit_message_text("📋 Список читов (нажмите для удаления):", user_id, call.message.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("❌ Нет добавленных читов", user_id, call.message.message_id)
    
    elif data.startswith('admin_delete_cheat_'):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Нет доступа!")
            return
        
        cheat_id = int(data.replace('admin_delete_cheat_', ''))
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cheats WHERE id = ?', (cheat_id,))
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, "✅ Чит удален!")
        bot.delete_message(user_id, call.message.message_id)
    
    elif data == 'admin_stats':
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "⛔ Нет доступа!")
            return
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM cheats')
        total_cheats = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "ru"')
        ru_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "en"')
        en_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "ua"')
        ua_users = cursor.fetchone()[0]
        
        conn.close()
        
        msg = f"""📊 Статистика бота:

👥 Всего пользователей: {total_users}
  - 🇷🇺 Русский: {ru_users}
  - 🇬🇧 English: {en_users}
  - 🇺🇦 Украинский: {ua_users}

🎮 Всего читов: {total_cheats}"""
        
        bot.edit_message_text(msg, user_id, call.message.message_id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    lang = result[0] if result else 'ru'
    conn.close()
    
    if text in ["📋 Список читов", "📋 Cheats List", "📋 Список читів"]:
        if not check_subscription(user_id):
            if lang == 'ru':
                msg = "📢 Для использования бота подпишитесь на канал:"
            elif lang == 'en':
                msg = "📢 To use the bot, subscribe to the channel:"
            else:
                msg = "📢 Для використання бота підпишіться на канал:"
            
            bot.send_message(user_id, msg, reply_markup=get_subscription_markup(user_id))
        else:
            if lang == 'ru':
                msg = "🎮 Выберите версию Minecraft:"
            elif lang == 'en':
                msg = "🎮 Choose Minecraft version:"
            else:
                msg = "🎮 Виберіть версію Minecraft:"
            
            bot.send_message(user_id, msg, reply_markup=get_versions_keyboard(user_id))
    
    elif text in ["⚙️ Настройки", "⚙️ Settings", "⚙️ Налаштування"]:
        if lang == 'ru':
            msg = "⚙️ Настройки бота:"
        elif lang == 'en':
            msg = "⚙️ Bot Settings:"
        else:
            msg = "⚙️ Налаштування бота:"
        
        bot.send_message(user_id, msg, reply_markup=get_settings_keyboard(user_id))

def process_add_cheat(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    try:
        data = message.text.split('\n')
        if len(data) < 5:
            bot.send_message(user_id, "❌ Неверный формат! Укажите все поля.")
            return
        
        name = data[0]
        version = data[1]
        description = data[2]
        download_link = data[3]
        instructions = data[4]
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cheats (name, version, description, download_link, instructions, added_date, added_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, version, description, download_link, instructions, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        conn.close()
        
        bot.send_message(user_id, f"✅ Чит \"{name}\" успешно добавлен!")
    
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {str(e)}")

def process_add_channel(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    try:
        channel_username, channel_link = message.text.split()
        
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channels (channel_username, channel_link, added_date)
            VALUES (?, ?, ?)
        ''', (channel_username, channel_link, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        bot.send_message(user_id, f"✅ Канал @{channel_username} добавлен!")
    
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {str(e)}")

if __name__ == '__main__':
    init_db()
    print("Бот запущен!")
    bot.polling(none_stop=True)