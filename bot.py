import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os
import urllib.parse
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------- USER STORAGE ---------------- #

def load_users():
    try:
        with open("users.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(list(users), f)

# ---------------- SEARCH IMDb ---------------- #

def search_imdb(movie_name):
    query = urllib.parse.quote(movie_name)
    first_letter = movie_name[0].lower()

    url = f"https://v3.sg.media-imdb.com/suggestion/{first_letter}/{query}.json"

    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return []

    data = res.json()

    results = []

    for item in data.get("d", []):
        title = item.get("l")
        imdb_id = item.get("id")
        year = item.get("y")
        poster = item.get("i", {}).get("imageUrl") if item.get("i") else None
        content_type = item.get("q")

        if content_type not in ["feature", "TV series", "movie"]:
            continue

        if title and imdb_id:
            results.append((title, imdb_id, year, poster))

        if len(results) >= 5:
            break

    return results

# ---------------- HANDLE MESSAGE ---------------- #

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text

    # ✅ TRACK USERS (SAFE)
    user = update.message.from_user
    user_id = user.id
    username = user.username

    users = load_users()

    if user_id not in users:
        users.add(user_id)
        save_users(users)

        print(f"🔥 New user: {username} | Total users: {len(users)}")

    # ---------------- SEARCH ---------------- #

    results = search_imdb(movie_name)

    if not results:
        await update.message.reply_text("❌ No results found")
        return

    context.user_data["results"] = results

    keyboard = []

    for title, imdb_id, year, poster in results:
        label = f"{title} ({year})" if year else title
        keyboard.append([InlineKeyboardButton(label, callback_data=imdb_id)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎬 Select your movie:",
        reply_markup=reply_markup
    )

# ---------------- BUTTON CLICK ---------------- #

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    imdb_id = query.data

    results = context.user_data.get("results", [])

    title = "Movie"
    year = ""
    poster = None

    for t, i, y, p in results:
        if i == imdb_id:
            title = t
            year = y
            poster = p
            break

    play_url = f"https://www.playimdb.com/title/{imdb_id}"

    keyboard = [
        [InlineKeyboardButton("▶️ Play", url=play_url)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"🎬 {title}"
    if year:
        caption += f" ({year})"

    caption += "\n\n💡 Tip:\nOpen player settings to change quality & enable subtitles"

    if poster:
        await query.message.reply_photo(
            photo=poster,
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        await query.message.reply_text(
            caption,
            reply_markup=reply_markup
        )

# ---------------- START BOT ---------------- #

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_button))

app.run_polling()
