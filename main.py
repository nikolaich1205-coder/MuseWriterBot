import telebot
import requests
import json
import os
from flask import Flask
from threading import Thread

# ===== НАСТРОЙКИ (Берутся из скрытых переменных) =====
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_KEY = os.environ.get('API_KEY')
FOLDER_ID = os.environ.get('FOLDER_ID')
FREE_LIMIT = 3  
YOUR_TG_NICK = "@nikolaich" 
# ====================================================

bot = telebot.TeleBot(BOT_TOKEN)
user_requests = {}

SYSTEM_PROMPT = "Ты — профессиональный копирайтер для Telegram-каналов. Пиши engaging-посты: цепляющий заголовок, короткие абзацы, эмодзи, призыв к действию. Тон — дружелюбный и экспертный. Не используй символы ** (звездочки) для выделения текста."

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Привет! Я твой ИИ-копирайтер. Напиши мне тему, и я сгенерирую для тебя пост! ✍️\n\n(У тебя есть 3 бесплатные генерации).")

@bot.message_handler(func=lambda message: True)
def generate_text(message):
    user_id = message.from_user.id
    
    if user_id not in user_requests:
        user_requests[user_id] = 0
        
    if user_requests[user_id] >= FREE_LIMIT:
        bot.reply_to(message, f"❌ Ваши 3 бесплатные генерации закончились!\n\nЧтобы продолжить пользоваться ботом, напишите мне: {YOUR_TG_NICK}")
        return 

    bot.send_message(message.chat.id, "Генерирую текст... ⏳")
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": "1000"},
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": message.text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        bot_text = result['result']['alternatives'][0]['message']['text']
        
        user_requests[user_id] += 1
        left = FREE_LIMIT - user_requests[user_id]
        
        bot.reply_to(message, f"{bot_text}\n\n---\n*Осталось бесплатных генераций: {left}*")
        
    except Exception as e:
        bot.reply_to(message, f"Ой, произошла ошибка: {e}")

# --- ВЕБ-СЕРВЕР (чтобы Render не выключал бота) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive() 
    print("Бот запущен на хостинге!")
    bot.polling(none_stop=True)
