import telebot
import requests
import time
import sqlite3
from datetime import datetime, timedelta
import uuid
import re

# --- إعدادات البوت والمفاتيح الخاصة بك ---
BOT_TOKEN = "8804551025:AAHV_zYzX_TsFQiBwNaOZVMefL7TMgZDCm4"
ADMIN_ID = 8629412895  # الآيدي الخاص بك يا عزيز
API_KEY = "wgpt_e6a6842f811a6e56b37579cfc7398d5c6bf6fffbf6d1809f"
API_URL = "https://wormgpt.app/v1/chat/completions"

bot = telebot.TeleBot(BOT_TOKEN)

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('bot_factory.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            expiry_date TIMESTAMP,
            bot_token TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_codes (
            code TEXT PRIMARY KEY,
            duration_hours INTEGER,
            is_used INTEGER DEFAULT 0,
            created_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_24h', '5$')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_7d', '15$')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price_30d', '40$')")
    
    conn.commit()
    conn.close()

init_db()

def is_banned(user_id):
    conn = sqlite3.connect('bot_factory.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_user_subscription(user_id):
    conn = sqlite3.connect('bot_factory.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date, bot_token FROM subscriptions WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None, None, "غير مشترك"
    
    expiry_str, bot_token = row
    if not expiry_str:
        return None, bot_token, "منتهي"
        
    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    
    if now >= expiry_date:
        return 0, bot_token, "منتهي"
    
    remaining = expiry_date - now
    days = remaining.days
    hours = remaining.seconds // 3600
    
    return f"{days} أيام و {hours} ساعات", bot_token, "نشط"

# --- دالة إرسال النصوص الطويلة مقسمة بدون أخطاء ---
def send_long_message(chat_id, text):
    max_length = 4000
    if len(text) <= max_length:
        bot.send_message(chat_id, text)
    else:
        parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for part in parts:
            bot.send_message(chat_id, part)
            time.sleep(0.3)

# --- أمر البداية /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ عذراً، لقد تم حظرك من استخدام هذه المنصة.")
        return
        
    if user_id == ADMIN_ID:
        bot.reply_to(message, "أهلاً بك يا عزيز يا مالك المنصة 👑\nإليك لوحة التحكم المتقدمة والشاملة:", reply_markup=admin_keyboard())
        return

    time_left, user_bot, status = get_user_subscription(user_id)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🛒 طلب اشتراك / إرسال إيصال التحويل", callback_data="request_sub"))
    markup.add(telebot.types.InlineKeyboardButton("🔑 تفعيل كود اشتراك", callback_data="redeem_code"))
    markup.add(telebot.types.InlineKeyboardButton("🤖 التحدث مع الذكاء الاصطناعي (WormGPT)", callback_data="ai_chat"))
    
    welcome_text = f"""
أهلاً بك يا {name} في منصة عزيز الذكية 🚀

📊 **حالة اشتراكك:**
- الحالة: `{status}`
- الوقت المتبقي: `{time_left if status == 'نشط' else 'لا يوجد اشتراك فعال'}`
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

def admin_keyboard():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("📊 إحصائيات المنصة", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("👥 المشتركون النشطون", callback_data="active_users")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("⚡ تفعيل اشتراك يدوي", callback_data="manual_sub"),
        telebot.types.InlineKeyboardButton("⚙️ تعديل الأسعار", callback_data="edit_prices")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="lookup_user"),
        telebot.types.InlineKeyboardButton("📦 نسخة احتياطية", callback_data="db_backup")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user"),
        telebot.types.InlineKeyboardButton("✅ إلغاء حظر مستخدم", callback_data="unban_user")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("➕ كود 24 ساعة", callback_data="gen_24h"),
        telebot.types.InlineKeyboardButton("➕ كود 7 أيام", callback_data="gen_7d")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("➕ كود 30 يوم", callback_data="gen_30d"),
        telebot.types.InlineKeyboardButton("📢 إذاعة للجميع", callback_data="admin_broadcast")
    )
    return markup

# --- معالجة الأزرار والتفاعل ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "request_sub":
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'price_%'")
        prices = {k: v for k, v in cursor.fetchall()}
        conn.close()
        
        text = f"""
💳 **طريقة الاشتراك وطلب الكود:**
1. قم بتحويل المبلغ المناسب حسب الأسعار الحالية:
   - 24 ساعة: `{prices.get('price_24h', '5$')}`
   - 7 أيام: `{prices.get('price_7d', '15$')}`
   - 30 يوم: `{prices.get('price_30d', '40$')}`
2. أرسل **صورة الإيصال** أو طلبك هنا مباشرة.
3. سيتم تحويل طلبك لعزيز ليقوم بالرد عليك بكود التفعيل.

أرسل رسالتك الآن:
"""
        msg = bot.send_message(call.message.chat.id, text)
        bot.register_next_step_handler(msg, forward_to_admin)

    elif call.data == "redeem_code":
        msg = bot.send_message(call.message.chat.id, "أرسل كود التفعيل الخاص بك الآن:")
        bot.register_next_step_handler(msg, process_activation_code)

    elif call.data == "ai_chat":
        _, _, status = get_user_subscription(user_id)
        if status != "نشط":
            bot.answer_callback_query(call.id, "⚠️ اشتراكك منتهٍ! يرجى تفعيل اشتراك أولاً.", show_alert=True)
            return
        msg = bot.send_message(call.message.chat.id, "🤖 تفضل، اكتب سؤالك أو استفسارك وسأقوم بالرد عليك عبر WormGPT:")
        bot.register_next_step_handler(msg, handle_user_ai_chat)

    elif call.data == "admin_stats" and user_id == ADMIN_ID:
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM subscriptions")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM activation_codes WHERE is_used = 0")
        unused_codes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM banned_users")
        banned_count = cursor.fetchone()[0]
        conn.close()
        
        stats_text = f"""
📊 **إحصائيات منصة عزيز:**
- إجمالي المسجلين: `{total_users}`
- الكودات غير المستخدمة: `{unused_codes}`
- عدد المحظورين: `{banned_count}`
"""
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, stats_text, parse_mode="Markdown")

    elif call.data == "active_users" and user_id == ADMIN_ID:
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, expiry_date FROM subscriptions WHERE expiry_date > ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        active = cursor.fetchall()
        conn.close()
        
        if not active:
            bot.answer_callback_query(call.id, "لا توجد اشتراكات نشطة حالياً.", show_alert=True)
            return
            
        text = "👥 **المشتركون النشطون حالياً:**\n\n"
        for uid, uname, exp in active:
            text += f"👤 الآيدي: `{uid}` | المعرف: @{uname}\n⏳ ينتهي في: `{exp}`\n-------------------\n"
        bot.answer_callback_query(call.id)
        send_long_message(call.message.chat.id, text)

    elif call.data == "manual_sub" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "⚡ أرسل الآيدي وعدد الساعات بهذه الصيغة تماماً:\n`USER_ID HOURS`\nمثال:\n`8629412895 72`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_manual_sub)

    elif call.data == "edit_prices" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "⚙️ أرسل الأسعار الجديدة بالصيغة التالية:\n`price_24h price_7d price_30d`\nمثال:\n`5$ 15$ 40$`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_edit_prices)

    elif call.data == "lookup_user" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "🔍 أرسل آيدي المستخدم للبحث عن تفاصيله:")
        bot.register_next_step_handler(msg, process_lookup_user)

    elif call.data == "db_backup" and user_id == ADMIN_ID:
        bot.answer_callback_query(call.id, "📦 جاري إرسال النسخة الاحتياطية...")
        try:
            with open('bot_factory.db', 'rb') as db_file:
                bot.send_document(ADMIN_ID, db_file, caption="📦 **نسخة احتياطية لقاعدة البيانات**", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ فشل إرسال النسخة الاحتياطية: {e}")

    elif call.data == "ban_user" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "🚫 أرسل آيدي المستخدم المراد حظره:")
        bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "unban_user" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "✅ أرسل آيدي المستخدم المراد إلغاء حظره:")
        bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "admin_broadcast" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد إذاعتها لجميع المشتركين الآن:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data.startswith("gen_") and user_id == ADMIN_ID:
        duration_map = {"gen_24h": (24, "24 ساعة"), "gen_7d": (24*7, "7 أيام"), "gen_30d": (24*30, "30 يوم")}
        hours, label = duration_map[call.data]
        
        code = f"AZIZ-{uuid.uuid4().hex[:8].upper()}"
        
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activation_codes (code, duration_hours, created_at) VALUES (?, ?, ?)", 
                       (code, hours, datetime.now()))
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, "تم توليد الكود بنجاح!")
        bot.send_message(call.message.chat.id, f"✅ **كود جديد ({label}):**\n`{code}`", parse_mode="Markdown")

# --- دوال لوحة التحكم ---
def process_manual_sub(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        target_id = int(parts[0])
        hours = int(parts[1])
        
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date FROM subscriptions WHERE user_id = ?", (target_id,))
        sub_row = cursor.fetchone()
        
        now = datetime.now()
        if sub_row and sub_row[0]:
            current_expiry = datetime.strptime(sub_row[0], "%Y-%m-%d %H:%M:%S")
            if current_expiry > now:
                new_expiry = current_expiry + timedelta(hours=hours)
            else:
                new_expiry = now + timedelta(hours=hours)
        else:
            new_expiry = now + timedelta(hours=hours)
            
        cursor.execute('''
            INSERT INTO subscriptions (user_id, username, expiry_date) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET expiry_date = ?
        ''', (target_id, "Manual_Add", new_expiry.strftime("%Y-%m-%d %H:%M:%S"), new_expiry.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تم تفعيل الاشتراك للمستخدم `{target_id}` لمدة `{hours}` ساعة.")
        try:
            bot.send_message(target_id, f"🎉 تم تفعيل رصيدك/اشتراكك من قبل الإدارة (عزيز)!\nينتهي اشتراكك في: `{new_expiry.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")
        except:
            pass
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في الصيغة: {e}")

def process_lookup_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date, bot_token FROM subscriptions WHERE user_id = ?", (target_id,))
        sub = cursor.fetchone()
        
        banned = is_banned(target_id)
        conn.close()
        
        status = "محظور 🚫" if banned else "غير محظور ✅"
        if sub:
            exp, b_token = sub
            sub_status = f"نشط حتى `{exp}`" if exp else "منتهي"
        else:
            sub_status = "غير مسجل أو غير مشترك"
            
        info = f"""
🔍 **نتيجة البحث عن المستخدم:**
- الآيدي: `{target_id}`
- حالة الحظر: `{status}`
- حالة الاشتراك: `{sub_status}`
"""
        bot.reply_to(message, info, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في الآيدي المدخل: {e}")

def process_edit_prices(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        p24, p7d, p30d = parts[0], parts[1], parts[2]
        
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'price_24h'", (p24,))
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'price_7d'", (p7d,))
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'price_30d'", (p30d,))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ تم تحديث الأسعار بنجاح:\n- 24 ساعة: {p24}\n- 7 أيام: {p7d}\n- 30 يوم: {p30d}")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في تنسيق الأسعار.")

def process_ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (target_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ تم حظر المستخدم `{target_id}` بنجاح.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ بالآيدي: {e}")

def process_unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect('bot_factory.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ تم رفع الحظر عن المستخدم `{target_id}`.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ بالآيدي: {e}")

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_text = message.text
    conn = sqlite3.connect('bot_factory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM subscriptions")
    users = cursor.fetchall()
    conn.close()
    
    success = 0
    fail = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, f"📢 **إشعار من الإدارة:**\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
    bot.reply_to(message, f"✅ تم إرسال الإذاعة بنجاح!\n- وصلت إلى: {success} مستخدم\n- فشلت عند: {fail}")

# --- محادثة الذكاء الاصطناعي للعملاء ---
def handle_user_ai_chat(message):
    user_text = message.text
    if user_text.startswith('/'):
        return
        
    wait_msg = bot.reply_to(message, "جاري المعالجة والصياغة... ⏳")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "wormgpt-v1.5",  
        "messages": [{"role": "user", "content": user_text}]
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=45)
        res_data = response.json()
        
        if "choices" in res_data:
            reply_text = res_data["choices"][0]["message"]["content"]
        else:
            reply_text = f"خطأ من الخادم: {res_data}"
            
        # استخدام دالة إرسال الرسائل الطويلة لتفادي خطأ الطول في تيليجرام
        bot.delete_message(message.chat.id, wait_msg.message_id)
        send_long_message(message.chat.id, reply_text)
        
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=wait_msg.message_id, text=f"حدث خطأ: {e}")

# --- تحويل الرسائل لعزيز ---
def forward_to_admin(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        return
    username = message.from_user.username or "بدون معرف"
    name = message.from_user.first_name
    
    if user_id == ADMIN_ID:
        return
        
    bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    bot.send_message(ADMIN_ID, f"👤 المشترك: {name}\n🆔 الآيدي: `{user_id}`\n(قم بعمل Reply للرد عليه)", parse_mode="Markdown")
    bot.reply_to(message, "✅ تم إرسال رسالتك إلى عزيز بنجاح، انتظر الرد!")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message is not None)
def admin_reply_handler(message):
    reply_msg = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = re.search(r'(\d{5,})', reply_msg)
    if match:
        target_user_id = int(match.group(1))
        try:
            bot.send_message(target_user_id, f"💬 **رد الإدارة (عزيز):**\n{message.text}")
            bot.reply_to(message, "✅ تم إرسال الرد بنجاح!")
        except Exception as e:
            bot.reply_to(message, f"❌ فشل الإرسال: {e}")
    else:
        bot.reply_to(message, "❌ لم يتم التعرف على آيدي المستخدم.")

# --- تفعيل الكود ---
def process_activation_code(message):
    user_id = message.from_user.id
    code = message.text.strip()
    
    conn = sqlite3.connect('bot_factory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT duration_hours, is_used FROM activation_codes WHERE code = ?", (code,))
    row = cursor.fetchone()
    
    if not row:
        bot.reply_to(message, "❌ هذا الكود غير صالح.")
        conn.close()
        return
        
    duration_hours, is_used = row
    if is_used == 1:
        bot.reply_to(message, "⚠️ هذا الكود مستخدم مسبقاً.")
        conn.close()
        return
        
    cursor.execute("SELECT expiry_date FROM subscriptions WHERE user_id = ?", (user_id,))
    sub_row = cursor.fetchone()
    
    now = datetime.now()
    if sub_row and sub_row[0]:
        current_expiry = datetime.strptime(sub_row[0], "%Y-%m-%d %H:%M:%S")
        if current_expiry > now:
            new_expiry = current_expiry + timedelta(hours=duration_hours)
        else:
            new_expiry = now + timedelta(hours=duration_hours)
    else:
        new_expiry = now + timedelta(hours=duration_hours)
        
    cursor.execute('''
        INSERT INTO subscriptions (user_id, username, expiry_date) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET expiry_date = ?
    ''', (user_id, message.from_user.username, new_expiry.strftime("%Y-%m-%d %H:%M:%S"), new_expiry.strftime("%Y-%m-%d %H:%M:%S")))
    
    cursor.execute("UPDATE activation_codes SET is_used = 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, f"🎉 مبروك يا عزيزي! تم تفعيل اشتراكك بنجاح.\nينتهي في: `{new_expiry.strftime('%Y-%m-%d %H:%M')}`", parse_mode="Markdown")

if __name__ == "__main__":
    print("--- بوت عزيز يعمل الآن مع نظام حماية وطباعة النصوص الطويلة ---")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ انقطع الاتصال: {e}")
            print("🔄 جاري إعادة الاتصال خلال 5 ثواني...")
            time.sleep(5)