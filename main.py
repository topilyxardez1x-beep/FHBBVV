import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_USERNAME = 'topiluxarp'  # Канал для обязательной подписки
CHANNEL_LINK = 'https://t.me/topiluxarp'

bot = telebot.TeleBot(TOKEN)

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
    
    # Добавляем основной канал если его нет
    cursor.execute('SELECT COUNT(*) FROM channels WHERE channel_username = ?', (CHANNEL_USERNAME,))
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO channels (channel_username, channel_link, added_date) VALUES (?, ?, ?)',
                      (CHANNEL_USERNAME, CHANNEL_LINK, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
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

def get_versions_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
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

def get_settings_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_change_lang = types.InlineKeyboardButton("🌐 Сменить язык / Change Language", callback_data="change_lang")
    btn_channel = types.InlineKeyboardButton("📢 Наш канал", url=CHANNEL_LINK)
    markup.add(btn_change_lang, btn_channel)
    return markup

def check_subscription(user_id):
    """ТОЧНАЯ проверка подписки на канал"""
    try:
        # Используем get_chat_member для точной проверки
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        
        # Проверяем все возможные статусы
        if member.status in ['member', 'administrator', 'creator']:
            return True
        elif member.status in ['left', 'kicked', 'restricted']:
            return False
        else:
            return False
            
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        # Если бот не может проверить (например не админ канала), 
        # проверяем через другой метод
        try:
            chat = bot.get_chat(f"@{CHANNEL_USERNAME}")
            member_count = bot.get_chat_members_count(f"@{CHANNEL_USERNAME}")
            # Если канал существует, пробуем еще раз
            member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            return member.status in ['member', 'administrator', 'creator']
        except:
            return False

def get_subscription_markup():
    """Создает клавиатуру с кнопкой подписки и проверки"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Кнопка для подписки на канал
    btn_subscribe = types.InlineKeyboardButton(
        "📢 ПОДПИСАТЬСЯ НА КАНАЛ", 
        url=CHANNEL_LINK
    )
    markup.add(btn_subscribe)
    
    # Кнопка проверки подписки
    btn_check = types.InlineKeyboardButton(
        "✅ Я ПОДПИСАЛСЯ! Проверить", 
        callback_data="check_sub"
    )
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
    
    # Сначала проверяем подписку
    if check_subscription(user_id):
        bot.send_message(
            user_id,
            "🇷🇺 Выберите язык / 🇬🇧 Choose language / 🇺🇦 Виберіть мову:",
            reply_markup=get_language_keyboard()
        )
    else:
        bot.send_message(
            user_id,
            "⚠️ *ОБЯЗАТЕЛЬНАЯ ПОДПИСКА!*\n\n"
            "📢 Чтобы использовать бота, вы ДОЛЖНЫ подписаться на наш канал!\n\n"
            "1️⃣ Нажмите кнопку «ПОДПИСАТЬСЯ НА КАНАЛ»\n"
            "2️⃣ Подпишитесь на канал\n"
            "3️⃣ Вернитесь в бот и нажмите «Я ПОДПИСАЛСЯ!»",
            parse_mode="Markdown",
            reply_markup=get_subscription_markup()
        )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "⛔ У вас нет доступа к админ-панели!")
        return
    
    # Сначала проверяем подписку админа
    if not check_subscription(user_id):
        bot.send_message(
            user_id,
            "⚠️ Вы должны быть подписаны на канал чтобы использовать админ-панель!",
            reply_markup=get_subscription_markup()
        )
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
    
    # Проверка подписки при ЛЮБОМ действии
    if not check_subscription(user_id) and data not in ['check_sub', 'lang_ru', 'lang_en', 'lang_ua']:
        bot.answer_callback_query(
            call.id,
            "❌ Вы не подписаны на канал! Подпишитесь и попробуйте снова.",
            show_alert=True
        )
        return
    
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
        
        if selected_lang == 'ru':
            msg = "✅ Язык установлен: Русский\nИспользуйте меню для навигации:"
        elif selected_lang == 'en':
            msg = "✅ Language set: English\nUse the menu to navigate:"
        else:
            msg = "✅ Мову встановлено: Українська\nВикористовуйте меню для навігації:"
        
        bot.edit_message_text(msg, user_id, call.message.message_id)
        bot.send_message(user_id, "👇 Меню:", reply_markup=get_main_menu_keyboard(user_id))
    
    elif data == 'check_sub':
        # ДВОЙНАЯ проверка подписки
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
            bot.send_message(
                user_id,
                "🇷🇺 Выберите язык / 🇬🇧 Choose language / 🇺🇦 Виберіть мову:",
                reply_markup=get_language_keyboard()
            )
        else:
            # Если не подписан - даем инструкцию
            bot.answer_callback_query(
                call.id,
                "❌ ВЫ НЕ ПОДПИСАНЫ НА КАНАЛ!\n\n"
                "1. Нажмите 'ПОДПИСАТЬСЯ НА КАНАЛ'\n"
                "2. Нажмите 'Подписаться' в Telegram\n"
                "3. Вернитесь и нажмите 'Я ПОДПИСАЛСЯ!'",
                show_alert=True
            )
            
            # Обновляем сообщение с инструкцией
            bot.edit_message_text(
                "⚠️ *ПОДПИСКА НЕ ПОДТВЕРЖДЕНА!*\n\n"
                "📢 Вы все еще не подписаны на канал!\n\n"
                "1️⃣ Нажмите кнопку ниже 👇\n"
                "2️⃣ Подпишитесь на канал\n"
                "3️⃣ Вернитесь и нажмите «Я ПОДПИСАЛСЯ!»\n\n"
                "⚠️ Без подписки бот не работает!",
                user_id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=get_subscription_markup()
            )
    
    elif data.startswith('ver_'):
        # Дополнительная проверка подписки перед показом читов
        if not check_subscription(user_id):
            bot.answer_callback_query(call.id, "❌ Подпишитесь на канал!", show_alert=True)
            return
            
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
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE subscribed = 1')
        subscribed_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "ru"')
        ru_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "en"')
        en_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE language = "ua"')
        ua_users = cursor.fetchone()[0]
        
        conn.close()
        
        msg = f"""📊 Статистика бота:

👥 Всего пользователей: {total_users}
  - ✅ Подписаны: {subscribed_users}
  - ❌ Не подписаны: {total_users - subscribed_users}
  
🌐 По языкам:
  - 🇷🇺 Русский: {ru_users}
  - 🇬🇧 English: {en_users}
  - 🇺🇦 Украинский: {ua_users}

🎮 Всего читов: {total_cheats}"""
        
        bot.edit_message_text(msg, user_id, call.message.message_id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    
    # Проверка подписки при ЛЮБОМ действии
    if not check_subscription(user_id):
        bot.send_message(
            user_id,
            "⚠️ *ДОСТУП ЗАПРЕЩЕН!*\n\n"
            "📢 Вы не подписаны на канал @topiluxarp\n\n"
            "1️⃣ Нажмите кнопку «ПОДПИСАТЬСЯ НА КАНАЛ»\n"
            "2️⃣ Подпишитесь\n"
            "3️⃣ Нажмите «Я ПОДПИСАЛСЯ!»",
            parse_mode="Markdown",
            reply_markup=get_subscription_markup()
        )
        return
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    lang = result[0] if result else 'ru'
    conn.close()
    
    if text in ["📋 Список читов", "📋 Cheats List", "📋 Список читів"]:
        if lang == 'ru':
            msg = "🎮 Выберите версию Minecraft:"
        elif lang == 'en':
            msg = "🎮 Choose Minecraft version:"
        else:
            msg = "🎮 Виберіть версію Minecraft:"
        
        bot.send_message(user_id, msg, reply_markup=get_versions_keyboard())
    
    elif text in ["⚙️ Настройки", "⚙️ Settings", "⚙️ Налаштування"]:
        if lang == 'ru':
            msg = "⚙️ Настройки бота:"
        elif lang == 'en':
            msg = "⚙️ Bot Settings:"
        else:
            msg = "⚙️ Налаштування бота:"
        
        bot.send_message(user_id, msg, reply_markup=get_settings_keyboard())

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