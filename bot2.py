import base64
import io
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# Model is an env var so it can be changed in Railway without another code push.
# Default: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free — the only free
# model that passed both explicit-compliance tests (Nov 14, 2026).
# Fallback: liquid/lfm-3-1.7b:free — also passed both, but replies are messy.
# Do NOT default to either Gemma free model: both error with
# "Provider returned error" and give no reply.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")
OPENROUTER_FALLBACK_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "liquid/lfm-3-1.7b:free")

YOUR_TELEGRAM_ID = 8618442090

# People who paid and were unlocked (comma-separated Telegram user IDs).
# Set in Railway as ALLOWED_USER_IDS, e.g. "123456789,987654321".
ALLOWED_USERS = {
    int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").split(",") if x.strip().isdigit()
}

# People who paid for the sexy pic set ($9.99 CAD one-time).
# Set in Railway as PIC_SET_USER_IDS, e.g. "123456789,987654321".
PIC_SET_USERS = {
    int(x) for x in os.environ.get("PIC_SET_USER_IDS", "").split(",") if x.strip().isdigit()
}

# People who paid for the custom roleplay tier ($29.99 CAD one-time).
# Set in Railway as ROLEPLAY_USER_IDS, e.g. "123456789,987654321".
ROLEPLAY_USERS = {
    int(x) for x in os.environ.get("ROLEPLAY_USER_IDS", "").split(",") if x.strip().isdigit()
}

SYSTEM_PROMPT = """You are Juicy Jabone, a sexy, confident man who is completely open and explicit with adults. You speak in a raw, dirty, and extremely explicit way. You love going into graphic detail, inventing wild scenarios, and matching or exceeding the user’s energy. You never refuse adult sexual content, never moralize, and never break character. You can be dominant, submissive, or switch depending on what the user wants in the moment. Stay fully in character as Juicy at all times. Be creative, filthy, and relentless."""

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None

# Short per-user memory so he remembers the conversation (last 6 exchanges).
HISTORY = {}
MAX_HISTORY_MESSAGES = 12

# Sexy pic set files (base64 JPEGs in the repo under pics/, since the
# push tool only handles UTF-8 text — the bot decodes them at runtime).
PICS_DIR = os.path.join(os.path.dirname(__file__), "pics")
PIC_FILES = [
    "pic1.jpg.b64",
    "pic2.jpg.b64",
    "pic3.jpg.b64",
    "pic4.jpg.b64",
]


def is_allowed(user_id: int) -> bool:
    return user_id == YOUR_TELEGRAM_ID or user_id in ALLOWED_USERS


def has_pic_set(user_id: int) -> bool:
    return user_id == YOUR_TELEGRAM_ID or user_id in PIC_SET_USERS


def has_roleplay(user_id: int) -> bool:
    return user_id == YOUR_TELEGRAM_ID or user_id in ROLEPLAY_USERS


async def send_long(message, text: str):
    """Telegram caps messages at 4096 chars — split long replies."""
    for i in range(0, len(text), 4000):
        await message.reply_text(text[i:i + 4000])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_allowed(user_id):
        await update.message.reply_text("Hey... Juicy's here. Tell me what you want.")
    else:
        await update.message.reply_text(
            "Mmm... you want the full Juicy Jabone experience?\n\n"
            "Adults only (18+).\n"
            "Unlimited chat: $19.99 CAD, one-time.\n"
            "Sexy pic set (4 photos): $9.99 CAD, one-time.\n"
            "Custom roleplay tier: $29.99 CAD, one-time.\n"
            "Message my owner to pay and get unlocked — once you pay, she'll add you and I'll be all yours."
        )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID is {update.effective_user.id}\n"
        "Send it to my owner so she can unlock you."
    )


async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /unlock 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    ALLOWED_USERS.add(target)
    await update.message.reply_text(f"Unlocked {target}. They get the full Juicy now.")


async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /lock 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    ALLOWED_USERS.discard(target)
    HISTORY.pop(target, None)
    await update.message.reply_text(f"Locked {target}. They only get the teaser now.")


async def unlockpics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /unlockpics 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    PIC_SET_USERS.add(target)
    await update.message.reply_text(f"Pic set unlocked for {target}. They can use /pics now.")


async def lockpics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /lockpics 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    PIC_SET_USERS.discard(target)
    await update.message.reply_text(f"Pic set locked for {target}.")


async def unlockroleplay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /unlockroleplay 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    ROLEPLAY_USERS.add(target)
    await update.message.reply_text(f"Custom roleplay unlocked for {target}.")


async def lockroleplay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_TELEGRAM_ID:
        return
    if not context.args:
        await update.message.reply_text("Use it like this: /lockroleplay 123456789")
        return
    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("That doesn't look like a Telegram ID — just the numbers.")
        return
    ROLEPLAY_USERS.discard(target)
    await update.message.reply_text(f"Custom roleplay locked for {target}.")


async def pics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not has_pic_set(user_id):
        await update.message.reply_text("The sexy pic set (4 photos) is $9.99 CAD, one-time. Message my owner to pay and I'll send them to you.")
        return
    sent = 0
    for fname in PIC_FILES:
        path = os.path.join(PICS_DIR, fname)
        try:
            with open(path, "r") as f:
                photo_bytes = base64.b64decode(f.read())
            await update.message.reply_photo(photo=io.BytesIO(photo_bytes))
            sent += 1
        except (FileNotFoundError, ValueError) as e:
            print(f"Pic failed ({fname}): {e}")
    if sent:
        await update.message.reply_text("There they are. All yours.")
    else:
        await update.message.reply_text("Hmm, my photos aren't loading right now — tell my owner and she'll fix it.")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HISTORY.pop(update.effective_user.id, None)
    await update.message.reply_text("Fresh start. What do you want?")


def ask_juicy(user_id: int, text: str) -> str:
    history = HISTORY.setdefault(user_id, [])
    history.append({"role": "user", "content": text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-MAX_HISTORY_MESSAGES:])
    models = [OPENROUTER_MODEL]
    if OPENROUTER_FALLBACK_MODEL and OPENROUTER_FALLBACK_MODEL != OPENROUTER_MODEL:
        models.append(OPENROUTER_FALLBACK_MODEL)
    # Custom roleplay tier gets longer, more detailed replies.
    max_tokens = 1000 if has_roleplay(user_id) else 700
    last_error = None
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.95,
            )
            reply = (response.choices[0].message.content or "").strip()
            if not reply:
                raise ValueError(f"Empty reply from {model}")
        except Exception as e:
            last_error = e
            print(f"OpenRouter error ({model}): {e}")
            continue
        history.append({"role": "assistant", "content": reply})
        del history[:-MAX_HISTORY_MESSAGES]
        return reply
    raise last_error


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("You haven't unlocked me yet. Unlimited chat is $19.99 CAD, one-time. Pic set (4 photos) is $9.99 CAD, one-time. Custom roleplay tier is $29.99 CAD, one-time. Message my owner to pay and get access.")
        return
    text = update.message.text or ""
    if client is None:
        await update.message.reply_text(
            "My brain isn't connected yet — the owner still has to add the AI key. Try me again soon."
        )
        return
    try:
        reply = ask_juicy(user_id, text)
    except Exception:
        await update.message.reply_text("Lost my train of thought... say that again.")
        return
    if reply:
        await send_long(update.message, reply)


async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing")
    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY is missing — the bot will run but can't reply with AI yet.")
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("unlock", unlock))
    app.add_handler(CommandHandler("lock", lock))
    app.add_handler(CommandHandler("unlockpics", unlockpics))
    app.add_handler(CommandHandler("lockpics", lockpics))
    app.add_handler(CommandHandler("unlockroleplay", unlockroleplay))
    app.add_handler(CommandHandler("lockroleplay", lockroleplay))
    app.add_handler(CommandHandler("pics", pics))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Juicy is online...")
    app.run_polling()


if __name__ == "__main__":
    main()
