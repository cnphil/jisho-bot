#!/usr/bin/env python3
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
from lru import LRU
import logging
from time import gmtime, strftime
from functools import partial

from config import token
from dictionary import query_jisho, render_word
from anki import output_anki_tsv

version = '0.1.2'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

chat_recordings = LRU(128)

RECORDING = range(1)

def conv_search(in_state, query_text, bot, update):
    """ For conversations: Search message handler.
    """
    if query_text == None:
        query_text = update.message.text
    logger.info("User %s: %s", update.effective_user.username, query_text)
    message_back, definition = query_jisho(query_text)
    if in_state == RECORDING:
        recording = chat_recordings.get(update.effective_user.username)
        if recording == None:
            update.message.reply_text("Warning: your recording got reset, probably because idle time was too long.")
            recording = []
            chat_recordings[update.effective_user.username] = recording
        if definition != None:
            recording.append(definition)
        message_back += '\nRecorded ' + str(len(recording)) + ' items.'
    bot.send_message(chat_id=update.message.chat_id,
                     text=message_back,
                     parse_mode=telegram.ParseMode.MARKDOWN,
                     disable_web_page_preview=True)
    return in_state

def conv_unrecognized(bot, update):
    logger.info("User %s: %s", update.effective_user.username, update.message.text)
    update.message.reply_text('Unrecognized message')
    return RECORDING

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
    return -1  # end the conversation

def start(bot, update):
    """ Start command handler.
    /start
    """
    update.message.reply_text("こんにちは。私は辞書ボットです。version=" + version)

def search(bot, update, args):
    """ Search command handler.
    /search <word>
    """
    #if (update.effective_user == None) or (update.effective_user.username != 'philhu'):
    #    bot.send_message(chat_id=update.message.chat_id, text="この機能は @philhu さんだけが利用できます。I'm only reserved to @philhu at the moment.")
    #    return
    conv_search(None,  # no conversation state
                ' '.join(args),  # query text
                bot, update)

def unknown(bot, update):
    """ Unknown message handler.
    Private chats: queries the message text
    Other chats (group): needs keywords to trigger search, $keywords$<word>
    """
    if update.message.chat.type == 'private':
        conv_search(None,  # no conversation state
                    None,  # use message text as query text
                    bot, update)
        return
    keywords = ["日语", "日本語", "japanese"]
    for keyword in keywords:
        if keyword in update.message.text:
            conv_search(None,  # no conversation state
                        update.message.text.split(keyword)[1],  # query text
                        bot, update)
            return

def main():
    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # conversation handler
    conv_handler = ConversationHandler(
            entry_points=[CommandHandler('record', conv_record)],

            states={
                RECORDING: [CommandHandler('record_stop', conv_record_stop),
                            MessageHandler(Filters.text, partial(conv_search, RECORDING, None))
                           ]
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
