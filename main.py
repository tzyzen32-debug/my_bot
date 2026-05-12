import telebot
import os
from flask import Flask

# I-setup ang Bot at Flask
TOKEN = "8761481105:AAF-dwHd9g4ZOG0HDlfDRTag4kWEcSTw7oU"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "verified_ids.txt"

# Siguraduhing existing ang file
if not os.path.exists(DATA_FILE):
    open(DATA_FILE, 'w').close()

def get_verified_ids():
    with open(DATA_FILE, "r") as f:
        return f.read().splitlines()

# --- WEB API PARA SA LUA APP ---
@app.route('/check/<user_id>', methods=['GET'])
def check_id(user_id):
    ids = get_verified_ids()
    if user_id in ids:
        return "VERIFIED", 200
    return "DENIED", 403

# --- TELEGRAM BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Zenkai Protect System\nGamitin ang /add [ID] para magbigay ng access.")

@bot.message_handler(commands=['add'])
def add_id(message):
    try:
        new_id = message.text.split()[1]
        ids = get_verified_ids()
        if new_id not in ids:
            with open(DATA_FILE, "a") as f:
                f.write(f"{new_id}\n")
            bot.reply_to(message, f"✅ Success: ID {new_id} is now verified.")
        else:
            bot.reply_to(message, "ℹ️ ID is already in the list.")
    except IndexError:
        bot.reply_to(message, "❌ Format: /add [ID_DITO]")

# Para tumakbo ang dalawa sa Railway
if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: bot.infinity_polling()).start()
    # Railway uses port 8080 by default
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
