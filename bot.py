import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔍 Search IMDb
def search_imdb(movie_name):
    import urllib.parse

    query = urllib.parse.quote(movie_name)
    first_letter = movie_name[0].lower()

    url = f"https://v3.sg.media-imdb.com/suggestion/{first_letter}/{query}.json"

    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return []

    data = res.json()

    results = []

    for item in data.get("d", [])[:5]:
        title = item.get("l")
        imdb_id = item.get("id")

        if title and imdb_id:
            results.append((title, imdb_id))

    return results


# 🤖 Handle message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text

    results = search_imdb(movie_name)

    if not results:
        await update.message.reply_text("❌ No results found")
        return

    keyboard = []

    for title, imdb_id in results:
        keyboard.append([InlineKeyboardButton(title, callback_data=imdb_id)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎬 Select your movie:",
        reply_markup=reply_markup
    )


# 🎯 Button click
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    imdb_id = query.data

    play_url = f"https://www.playimdb.com/title/{imdb_id}"

    keyboard = [
        [InlineKeyboardButton("▶️ Play", url=play_url)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🎬 Here you go:",
        reply_markup=reply_markup
    )


# 🚀 Run bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_button))

app.run_polling()
