#!/usr/bin/env python3
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
from lru import LRU
import logging
from time import gmtime, strftime

from config import token
from dictionary import query_jisho, render_word
from anki import output_anki_tsv

version = '0.1.1'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

chat_recordings = LRU(128)

def search(bot, update, args):
    """ Search command handler.
    /search <word>
    """
    #if (update.effective_user == None) or (update.effective_user.username != 'philhu'):
    #    bot.send_message(chat_id=update.message.chat_id, text="この機能は @philhu さんだけが利用できます。I'm only reserved to @philhu at the moment.")
    #    return
    bot.send_message(chat_id=update.message.chat_id, text=query_jisho(' '.join(args))[0])

def unknown(bot, update):
    """ Unknown message handler.
    For capturing non-command messages in group chats.
    $keywords$<word>
    """
    keywords = ["日语", "日本語", "japanese"]
    for keyword in keywords:
        if keyword in update.message.text:
            search(bot, update, [update.message.text.split(keyword)[1]])
            return

GENERAL, RECORDING = range(2)

def conv_start(bot, update):
    """ For conversations: Start command handler.
    /start
    """
    update.message.reply_text("こんにちは。私は辞書ボットです。version=" + version)
    return GENERAL

def conv_search(bot, update, in_state):
    """ For conversations: Search message handler.
    """
    logger.info("User %s: %s", update.effective_user.username, update.message.text)
    message_back, definition = query_jisho(update.message.text)
    if in_state == GENERAL:
        update.message.reply_text(message_back)
    else:
        recording = chat_recordings.get(update.effective_user.username)
        if recording == None:
            update.message.reply_text("Warning: your recording got reset, probably because idle time was too long.")
            recording = []
            chat_recordings[update.effective_user.username] = recording
        if definition != None:
            recording.append(definition)
        message_back += '\nRecorded ' + str(len(recording)) + ' items.'
        update.message.reply_text(message_back)
    return in_state

# some handy bindings of conv_search
conv_search_general = lambda bot, update: conv_search(bot, update, GENERAL)
conv_search_recording = lambda bot, update: conv_search(bot, update, RECORDING)

def conv_unrecognized(bot, update):
    logger.info("User %s: %s", update.effective_user.username, update.message.text)
    update.message.reply_text('Unrecognized message')
    return GENERAL

def conv_record(bot, update):
    logger.info("User %s is now recording", update.effective_user.username)
    update.message.reply_text("Started recording.")
    chat_recordings[update.effective_user.username] = []
    return RECORDING

def conv_record_stop(bot, update):
    logger.info("User %s stopped recording", update.effective_user.username)
    definitions = chat_recordings[update.effective_user.username]
    update.message.reply_text("Recording stopped. " + str(len(definitions)) + " items.\n" + ', '.join(list(map(lambda d: render_word(d), definitions))))
    if len(definitions) > 0:
        with output_anki_tsv(definitions) as temp_filename:
            bot.send_document(chat_id=update.message.chat_id, document=open(temp_filename, 'rb'), filename="jisho_"+strftime("%Y%m%d_%H%M", gmtime())+".tsv")
    return GENERAL

def main():
    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    # conversation handler
    conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', conv_start),
                          CommandHandler('record', conv_record),
                          MessageHandler(Filters.text, conv_search_general)
                         ],

            states={
                GENERAL: [MessageHandler(Filters.text, conv_search_general),
                          CommandHandler('record', conv_record)
                         ],
                RECORDING: [CommandHandler('record_stop', conv_record_stop),
                            MessageHandler(Filters.text, conv_search_recording)]
            },

            fallbacks=[MessageHandler(Filters.text, conv_unrecognized)]
    )
    dispatcher.add_handler(conv_handler)

    # non-conversation (group chat) handlers
    search_handler = CommandHandler('search', search, pass_args=True)
    dispatcher.add_handler(search_handler)

    unknown_handler = MessageHandler(Filters.text, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

if __name__ == "__main__":
        main()
