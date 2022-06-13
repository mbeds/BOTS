#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardRemove
import logging
import json
import pymongo
from subprocess import PIPE, run
import random
import string
from paypalcheckoutsdk.orders import OrdersCreateRequest
from paypalhttp import HttpError
from paypalcheckoutsdk.orders import OrdersCaptureRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
import csv
import pandas as pd
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["datasets"]
# Creating Access Token for Sandbox
client_id = ""
client_secret = ""
# Creating an environment
environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
client = PayPalHttpClient(environment)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

TOKEN = ""
KEYWORD = ""
orderid = ""
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hi! Welcome to BusinessAnalytica.io @PropertyLookupBOT.')
    context.bot.send_message(chat_id=update.effective_chat.id, text='\n\nThe property bot is able to search the HM land registry for company owned propeties and land, and output the data to a spreadsheet.  The bot costs just £10 via paypal')
    #context.bot.send_message(chat_id=update.effective_chat.id, text=#str(pay()))
    context.bot.send_message(chat_id=update.effective_chat.id, text='Open the link in your browser and When paid type /lookup (KEYWORD) for example /lookup Birmingham')

def pay():
  global orderid
  request = OrdersCreateRequest()
  request.prefer('return=representation')
  request.request_body (
    {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "GBP",
                    "value": "10.00"
                }
            }
         ],
         "application_context": {
           "return_url": "",
           "brand_name": "",
           "landing_page": "BILLING",
           "user_action": "CONTINUE"
                }
    }
  )

  try:
    response = client.execute(request)
    for link in response.result.links:
      try:
        if link.rel == "approve":
          orderid=response.result.id
          return link.href
      except:
        pass
  except:
    pass
    
def check_pay(update, context):
  request = OrdersCaptureRequest(orderid)
  response = client.execute(request)
  order = response.result.id
  if response.result.status == "COMPLETED":
    get_keyword(update, context)
  else:
    context.bot.send_message(chat_id=update.effective_chat.id, text='Please pay the invoice')

def get_keyword(update,context):
    global KEYWORD
    KEYWORD = update.message.text.split(" ")[1]
    command(update, context)


def command(update, context):
    print(KEYWORD)
    mycol = mydb["hmland_05_2021"]
    context.bot.send_message(chat_id=update.effective_chat.id,text="Searching for "+str(KEYWORD))
    context.bot.send_message(chat_id=update.effective_chat.id,text="Please Wait")
    list = []
    letters = string.ascii_lowercase
    file2= ''.join(random.choice(letters) for i in range(9))+".csv"
    print("Generating File: "+file2)
    result = mycol.find()
    for row in result:
      if KEYWORD in str(row):
        print(row)
        list.append(row)

    context.bot.send_message(chat_id=update.effective_chat.id,text="Data loaded")
    data=pd.DataFrame.from_dict(list)
    try:
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data.to_string()))
    except:
      pass

    try:
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data.head(1)))
    except:
      pass

    try:
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data["Property Address"]))
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data["Proprietor Name (1)"]))
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data["Company Registration No"]))
    except:
      pass

    try:
      context.bot.send_message(chat_id=update.effective_chat.id,text=str(data.describe()))

    except:
      pass
#    for i in list:
#      a = writer.writerow(i)
#      print(i)

def error(update, context, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    # Start the bot.
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN, use_context = True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
#    dp.add_handler(CommandHandler("lookup", check_pay))
    dp.add_handler(CommandHandler("lookup", get_keyword))
    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.text, command))
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
