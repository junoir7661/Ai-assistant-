"""
Ankit Chat Automation Bot — python-telegram-bot (HTTPS, Telethon nahi)
---------------------------------------------------------------------------
Telethon MTProto use karta hai jo kai baar Render jaise free hosting ke IP
se block ho jata hai (isliye "Telegram is having internal issues" error aata
rehta tha). Ye version python-telegram-bot library use karta hai jo normal
HTTPS se Telegram Bot API ko baat karta hai — zyada reliable hai.

Ye bot Telegram ke "Chat Automation" (Settings -> Business -> Chat
Automation) feature me add hota hai. Wahan Telegram khud decide karta hai
kab ye bot aapki taraf se reply kare (jab aap away/busy ho).

RENDER PAR DEPLOY (FREE Web Service):
1) @BotFather se bot banao -> BOT_TOKEN lo.
2) Apni Telegram user id lo (e.g. @userinfobot se) -> OWNER_ID.
3) Render environment variables me daalo: BOT_TOKEN, GEMINI_API_KEY, OWNER_ID
4) Start command: python ankit_offline_bot.py
5) Telegram Settings -> Business -> Chat Automation me jaake apna bot
   username add karo ("All private chats except...").
6) Render free service ko sleep se bachane ke liye UptimeRobot se "/" URL
   ko har 5-10 min ping karte raho.
"""

import os
import asyncio
import threading

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

import google.generativeai as genai

# ====== ENV VARIABLES (Render dashboard me set karo) ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")       # BotFather se mila token
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))   # aapki Telegram user id (control commands ke liye)
OWNER_NAME = "Ankit"
PORT = int(os.environ.get("PORT", "10000"))
# ============================================================

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot_enabled = True  # /off se band, /on se chalu

# ---------- Render ko "zinda" dikhane ke liye chhota web server ----------
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return "Ankit chat automation bot is running."


def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)


# --------------------------------------------------------------------------


async def ai_reply(user_text: str) -> str:
    prompt = (
        f"Tum {OWNER_NAME} ki taraf se casual, friendly Hinglish me chat kar rahe ho. "
        f"Normal insaan jaisa short reply do, robot jaisa mat lagna.\n\n"
        f"Doosre insaan ka message: {user_text}"
    )
    try:
        resp = await asyncio.to_thread(model.generate_content, prompt)
        return resp.text.strip()
    except Exception:
        return "abhi thoda busy hu, thodi der me baat karta hu."


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if update.effective_user.id != OWNER_ID:
        return
    bot_enabled = True
    await update.message.reply_text(
        f"Bot: shuru ho gaya, {OWNER_NAME}!\n\n"
        "Commands:\n"
        "/on - auto-reply chalu karo\n"
        "/off - auto-reply band karo\n"
        "/status - current status dekho\n"
        "/help - ye list dobara dekho"
    )


async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if update.effective_user.id != OWNER_ID:
        return
    bot_enabled = True
    await update.message.reply_text("Bot: auto-reply ON kar diya.")


async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if update.effective_user.id != OWNER_ID:
        return
    bot_enabled = False
    await update.message.reply_text("Bot: auto-reply OFF kar diya.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(f"Bot status: {'ON' if bot_enabled else 'OFF'}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "Commands:\n"
        "/on - auto-reply chalu karo\n"
        "/off - auto-reply band karo\n"
        "/status - current status dekho"
    )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_enabled:
        return
    text = update.message.text or ""
    reply_text = await ai_reply(text)
    await update.message.reply_text(f"Bot: {reply_text}")


def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("on", cmd_on))
    app.add_handler(CommandHandler("off", cmd_off))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    print("Bot chalu ho gaya (python-telegram-bot).")
    app.run_polling()


if __name__ == "__main__":
    main()
