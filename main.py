import telebot
import os
from flask import Flask
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = "8761481105:AAF-dwHd9g4ZOG0HDlfDRTag4kWEcSTw7oU"
ADMIN_ID = 6763595343  # Your Verified Admin ID
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "verified_ids.txt"
SETTINGS_FILE = "settings.txt"

# Ensure files exist
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
    with open(DATA_FILE, "r") as f:
        for line in f:
            if "|" in line:
                uid, expiry = line.strip().split("|")
                data[uid] = expiry
    return data

def save_id(uid, days):
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
@bot.message_handler(commands=['setdays'])
def admin_set_days(message):
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
def admin_add_id(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_id = message.text.split()[1]
            current_setting = get_default_days()
            expiry = save_id(new_id, current_setting)
            
            success_msg = f"""
╔════════════════════╗
⚡️  [ACCESS GRANTED]  ⚡️
╚════════════════════╝

Registration: **SUCCESS**
Validity: **{current_setting} Days**
Expires on: **{expiry}**

╔════════════════════╗

🆔 {new_id}

╚════════════════════╝
            """
            bot.reply_to(message, success_msg)
        except:
            bot.reply_to(message, "❌ Usage: `/add [ID]`")
    else:
        bot.reply_to(message, "🚫 You are not authorized.")

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
