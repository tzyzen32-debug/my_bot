import telebot
import os
import re
from flask import Flask
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = "8761481105:AAF-dwHd9g4ZOG0HDlfDRTag4kWEcSTw7oU"
ADMIN_ID = 6763595343  # Iyong Verified Admin ID
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "verified_ids.txt"
SETTINGS_FILE = "settings.txt"

# Siguraduhing existing ang mga files
for f in [DATA_FILE, SETTINGS_FILE]:
    if not os.path.exists(f):
        open(f, 'w').close()

def get_default_days():
    try:
        with open(SETTINGS_FILE, "r") as f:
            val = f.read().strip()
            return int(val) if val else 7
    except:
        return 7

def set_default_days(days):
    with open(SETTINGS_FILE, "w") as f:
        f.write(str(days))

def get_verified_data():
    data = {}
    if not os.path.exists(DATA_FILE):
        return data
    with open(DATA_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                uid, expiry = line.split("|")
                data[uid] = expiry
    return data

def save_id(uid, days):
    # Check kung existing na para hindi doble
    data = get_verified_data()
    if uid in data:
        return "ALREADY_EXISTS"
    
    expiry_date = (datetime.now() + timedelta(days=int(days))).strftime("%Y-%m-%d")
    with open(DATA_FILE, "a") as f:
        f.write(f"{uid}|{expiry_date}\n")
    return expiry_date

# --- WEB API ---
@app.route('/check/<user_id>', methods=['GET'])
def check_id(user_id):
    data = get_verified_data()
    if user_id in data:
        expiry_str = data[user_id]
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        if datetime.now().date() <= expiry_date.date():
            return f"VERIFIED|{expiry_str}", 200
        else:
            return "EXPIRED", 403
    return "DENIED", 403

# --- BOT COMMANDS ---

# DYNAMIC QUOTE LOGIC (Heto ang dinagdag ko base sa gusto mo)
@bot.message_handler(func=lambda message: message.text and message.text.lower().startswith("hello"))
def dynamic_shoutout(message):
    if message.from_user.id == ADMIN_ID:
        match = re.search(r'"([^"]*)"', message.text)
        if match:
            custom_text = match.group(1)
            if "si" in message.text.lower():
                try:
                    parts = message.text.lower().split("si")
                    target_name = message.text[len(parts[0]) + 3:].strip()
                    target_name = re.sub(r'"([^"]*)"', '', target_name).strip()
                    bot.send_message(message.chat.id, f"{custom_text} {target_name}")
                except:
                    bot.send_message(message.chat.id, custom_text)
            else:
                bot.send_message(message.chat.id, custom_text)

@bot.message_handler(commands=['idlist'])
def admin_id_list(message):
    """Admin only: List all registered IDs"""
    if message.from_user.id == ADMIN_ID:
        data = get_verified_data()
        if not data:
            bot.reply_to(message, "📂 Walang IDs sa database.")
            return
        
        output = "📋 **REGISTERED IDs:**\n\n"
        for uid, exp in data.items():
            output += f"🆔 `{uid}` — 📅 {exp}\n"
        bot.reply_to(message, output, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🚫 Admin only command.")

@bot.message_handler(commands=['setdays'])
def admin_set_days(message):
    """Admin only: Change default expiry days"""
    if message.from_user.id == ADMIN_ID:
        try:
            days = int(message.text.split()[1])
            set_default_days(days)
            bot.reply_to(message, f"⚙️ **Admin Panel:** New registration period set to **{days} days**.")
        except:
            bot.reply_to(message, "❌ Usage: `/setdays [number]`")
    else:
        bot.reply_to(message, "🚫 You are not authorized.")

@bot.message_handler(commands=['add'])
def public_add_id(message):
    """Public: Anyone can register an ID"""
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Usage: `/add [ID]`")
            return

        new_id = args[1]
        current_setting = get_default_days()
        result = save_id(new_id, current_setting)
        
        if result == "ALREADY_EXISTS":
            bot.reply_to(message, f"⚠️ ID `{new_id}` already use registered.")
            return

        success_msg = f"""
╔═════════════╗
⚡️  [ACCESS GRANTED]  ⚡️
╚═════════════╝

Registration: **SUCCESS**
Validity: **{current_setting} Days**
Expires on: **{result}**

╔══════╗

🆔 {new_id}

╚══════╝
        """
        bot.reply_to(message, success_msg)
    except Exception as e:
        bot.reply_to(message, "❌ error not register ID.")

if __name__ == "__main__":
    from threading import Thread
    print("Bot is starting...")
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
