from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import urllib.request, json
import urllib.parse
import config

version = '0.0.3'
updater = Updater(token=config.token)

dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

def extract_def(data):
    word = ''
    reading = ''
    parts_of_speech = ''
    english_definitions = ''
    if 'word' in data['data'][0]['japanese'][0]:
        word = data['data'][0]['japanese'][0]['word']
    if 'reading' in data['data'][0]['japanese'][0]:
        reading = data['data'][0]['japanese'][0]['reading']
    if 'parts_of_speech' in data['data'][0]['senses'][0]:
        parts_of_speech = ', '.join(data['data'][0]['senses'][0]['parts_of_speech'])
    if 'english_definitions' in data['data'][0]['senses'][0]:
        english_definitions = ', '.join(data['data'][0]['senses'][0]['english_definitions'])
    return word + '（' + reading + '）\n' + parts_of_speech + ': ' + english_definitions

def query_jisho(query):
    query_url = "https://jisho.org/api/v1/search/words?keyword=" + urllib.parse.quote(query)
    print(query_url)
    with urllib.request.urlopen(query_url) as url:
        data = json.loads(url.read().decode())
        if (data['meta']['status'] != 200) or (len(data['data']) == 0):
            return '見つからない。'
        else:
            return extract_def(data)
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="こんにちは。私は辞書ボットです。version=" + version)

def search(bot, update, args):
    #if (update.effective_user == None) or (update.effective_user.username != 'philhu'):
    #    bot.send_message(chat_id=update.message.chat_id, text="この機能は @philhu さんだけが利用できます。I'm only reserved to @philhu at the moment.")
    #    return
    bot.send_message(chat_id=update.message.chat_id, text=query_jisho(' '.join(args)))

def unknown(bot, update):
    # print(update.message.text)
    keywords = ["日语", "日本語", "japanese"]
    for keyword in keywords:
        if keyword in update.message.text:
            search(bot, update, [update.message.text.split(keyword)[1]])
            return

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

search_handler = CommandHandler('search', search, pass_args=True)
dispatcher.add_handler(search_handler)

unknown_handler = MessageHandler(Filters.text, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
