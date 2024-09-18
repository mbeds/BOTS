

import os
import telebot
import ollama
import asyncio
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry  # Updated import statement

model = "tinyllama"
BOT_TOKEN = ''

LOG_FILE = "bot_logs.txt"

pre = """  """
post = """ """

bot = telebot.TeleBot(BOT_TOKEN)

async def askai(query):
    response = ollama.chat(model=model, messages=[{'role': 'user',
                                                   'content': pre + query + post}])
    return response['message']['content']


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    try:
        bot.reply_to(message, "Hello, I am running model " + model + ". Please enter your query.")
    except telebot.apihelper.ApiTelegramException as e:
        if "Forbidden: bot was blocked by the user" in e.description:
            # User has blocked the bot
            print(f"User {message.from_user.username} has blocked the bot.")
            # You can handle this situation as per your requirements, e.g., log the occurrence
        else:
            # Handle other API exceptions
            print(f"An error occurred: {e}")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    if "/query" in message.text:
        bot.reply_to(message, "Processing query please wait...")
        asyncio.run(handle_message(message))

async def handle_message(message):
    retries = 300
    for attempt in range(retries):
        try:
            response = await askai(message.text)
            with open(LOG_FILE, "a") as file:
                file.write(f"User: {message.from_user.username}, Query: {message.text}, Answer: {response}\n")
            bot.reply_to(message, str(response))
            break
        except requests.Timeout:
            bot.reply_to(message, "Sorry, the connection to the AI service timed out. Retrying...")
        except Exception as e:
            if attempt < retries - 1:
                bot.reply_to(message, f"Sorry, the AI service is busy. Retrying... Attempt {attempt + 1}/{retries}")
            else:
                bot.reply_to(message, "Sorry, the AI service is currently busy. Please try again later.")


if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w"):
            pass

    retries = Retry(total=30, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))

    while True:
        try:
            bot.polling()
        except Exception as e:
            print(f"An error occurred: {e}")
