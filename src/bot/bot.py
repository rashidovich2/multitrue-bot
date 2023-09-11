import os
import sys

import json
import logging
import pathlib

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
KEY_PATH = pathlib.Path(os.path.dirname(__file__), "../..")

from news.collector import NewsAPICollector

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def start(update, context):
    user = update.message.from_user
    logger.info(f"User {user} started the conversation.")
    for i, v in vars(user).items():
        context.user_data[i] = v

    welcome_message = f"Hello, {user.first_name}\nThis is JC News bot🗞️🤖\n\nYou can get Top News Headlines for a Country and a Category from here. \n\n"
    print(context)
    keyborad = [
        [
            InlineKeyboardButton("🇺🇸", callback_data="us"),
            InlineKeyboardButton("🇯🇵", callback_data="jp"),
            InlineKeyboardButton("🇹🇼", callback_data="tw"),
        ],
        [
            InlineKeyboardButton("🇰🇷", callback_data="kr"),
            InlineKeyboardButton("🇬🇧", callback_data="gb"),
            InlineKeyboardButton("🇨🇳", callback_data="cn"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyborad)
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)
    update.message.reply_text("Please Choose a Country🤖", reply_markup=reply_markup)

    return "CATEGORY"


def start_over(update, context):

    keyborad = [
        [
            InlineKeyboardButton("🇺🇸", callback_data="us"),
            InlineKeyboardButton("🇯🇵", callback_data="jp"),
            InlineKeyboardButton("🇹🇼", callback_data="tw"),
        ],
        [
            InlineKeyboardButton("🇰🇷", callback_data="kr"),
            InlineKeyboardButton("🇬🇧", callback_data="gb"),
            InlineKeyboardButton("🇨🇳", callback_data="cn"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyborad)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Please Choose a Country🤖", reply_markup=reply_markup
    )

    return "CATEGORY"


def select_category(update, context):
    logger.info(f"User data from context {context.user_data}")
    logger.info(f"Chat data from context {context.chat_data}")
    logger.info(f"Bot data from context {context.bot_data}")

    query = update.callback_query
    query.answer()
    country = query.data
    keyborad = [
        [
            InlineKeyboardButton(
                "👩🏼‍💻Technology", callback_data=f"{country} technology"
            ),
            InlineKeyboardButton(
                "🧑‍💼Business", callback_data=f"{country} business"
            ),
        ],
        [
            InlineKeyboardButton(
                "👨🏻‍🎤Entertainment", callback_data=f"{country} entertainment"
            ),
            InlineKeyboardButton(
                "👩🏻‍⚕️Health", callback_data=f"{country} health"
            ),
        ],
        [
            InlineKeyboardButton(
                "👨🏿‍🔬Science", callback_data=f"{country} science"
            ),
            InlineKeyboardButton(
                "🏋🏼‍♂️Sports", callback_data=f"{country} sports"
            ),
        ],
        [InlineKeyboardButton("🌎General", callback_data=f"{country} general")],
    ]
    reply_markup = InlineKeyboardMarkup(keyborad)
    query.edit_message_text(text="Please Choose a Category🤖", reply_markup=reply_markup)

    return "HEADLINES"


def get_news(update, context):
    query = update.callback_query
    query.answer()
    country, category = query.data.split(" ")

    nac = NewsAPICollector(country=country, category=category, page_size=10, print_format="telebot")
    nac.collcet_news()
    news_list = nac.news_list

    news_list = news_list[:5] if len(news_list) > 5 else news_list

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Top {len(news_list)} latest news of [{country.upper()}] [{category.upper()}] for you🤖",
    )

    for news in news_list:
        context.bot.send_message(chat_id=update.effective_chat.id, text=news)

    keyboard = [
        [
            InlineKeyboardButton("Let's do it again!", callback_data="start over"),
            InlineKeyboardButton("I've had enough...", callback_data="end"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Do you want to start over?🤖",
        reply_markup=reply_markup,
    )

    return "START OVER OR NOT"


def end(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="See you next time!🤖")
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="(Type '/start' to restart me)🤖",
    )

    return ConversationHandler.END


def main():
    updater = Updater(
        token=json.load(open(KEY_PATH / "keys.json", "r"))["telegram_key"],
        use_context=True,
    )

    dispatcher = updater.dispatcher
    country_pattern = "^us|jp|cn|tw|kr|gb$"
    headlines_pattern = "^us|jp|cn|tw|kr|gb business|entertainment|general|health|science|sports|technology|$"

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "CATEGORY": [CallbackQueryHandler(select_category, pattern=country_pattern)],
            "HEADLINES": [CallbackQueryHandler(get_news, pattern=headlines_pattern)],
            "START OVER OR NOT": [
                CallbackQueryHandler(start_over, pattern="^start over$"),
                CallbackQueryHandler(end, pattern="^end$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
