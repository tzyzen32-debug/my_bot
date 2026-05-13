import telebot
import os
import requests
from flask import Flask
from datetime import datetime, timedelta
from threading import Thread

# --- CONFIGURATION ---
TOKEN = "8761481105:AAF-dwHd9g4ZOG0HDlfDRTag4kWEcSTw7oU"
ADMIN_ID = 6763595343  # Your Verified Admin ID
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- JSONBIN CONFIGURATION ---
JSONBIN_ID = "6a045ab4c0954111d818cdd9"
JSONBIN_API_KEY = "$2a$10$YmXKZU4F0UjFeOAY3CPuXeg9OsECrYk2zN4eb65PW8YSAYfFxM6Mq"
JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

# --- DATABASE FUNCTIONS (CLOUD STORAGE) ---

def get_remote_data():
    """Fetch data from JSONBin Cloud"""
    try:
        response = requests.get(f"{JSONBIN_URL}/latest", headers=HEADERS)
        if response.status_code == 200:
            return response.json()["record"]
        else:
            return {"verified_ids": {}, "default_days": 7}
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"verified_ids": {}, "default_days": 7}

def save_remote_data(data):
    """Save data to JSONBin Cloud"""
    try:
        requests.put(JSONBIN_URL, headers=HEADERS, json=data)
    except Exception as e:
        print(f"Error saving data: {e}")

def get_default_days():
    data = get_remote_data()
    try:
        return int(data.get("default_days", 7))
    except:
        return 7

def set_default_days(days):
    data = get_remote_data()
    data["default_days"] = int(days)
    save_remote_data(data)

def get_verified_data():
    data = get_remote_data()
    return data.get("verified_ids", {})

def save_id(uid, days):
    full_data = get_remote_data()
    verified_ids = full_data.get("verified_ids", {})

    if str(uid) in verified_ids:
        return "ALREADY_EXISTS"
    
    expiry_date = (datetime.now() + timedelta(days=int(days))).strftime("%Y-%m-%d")
    verified_ids[str(uid)] = expiry_date
    
    full_data["verified_ids"] = verified_ids
    save_remote_data(full_data)
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

@bot.message_handler(commands=['idlist'])
def admin_id_list(message):
    """Admin only: List all registered IDs"""
    if message.from_user.id == ADMIN_ID:
        data = get_verified_data()
        if not data:
            bot.reply_to(message, "📂 No IDs found in the database.")
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
            bot.reply_to(message, f"⚠️ The ID `{new_id}` is already registered.")
            return

        success_msg = f"""
╔═══════════╗
⚡️[ACCESS GRANTED] ⚡️
╚═══════════╝

Registration: **SUCCESS**
Validity: **{current_setting} Days**
Expires on: **{result}**

╔═════╗

🆔 {new_id}

╚═════╝
        """
        bot.reply_to(message, success_msg)
    except Exception as e:
        bot.reply_to(message, "❌ An error occurred while adding the ID.")

if __name__ == "__main__":
    print("Bot is starting with Cloud JSON storage...")
    # Thread for Bot Polling
    Thread(target=lambda: bot.infinity_polling()).start()
    # Flask Server for API
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
