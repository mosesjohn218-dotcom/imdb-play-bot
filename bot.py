import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔍 Search IMDb
def search_imdb(movie_name):
    url = "https://www.imdb.com/find"
    params = {"q": movie_name}
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    rows = soup.select("td.result_text a")

    for r in rows[:5]:
        title = r.text
        href = r["href"]
        imdb_id = href.split("/")[2]

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
