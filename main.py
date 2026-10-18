import os
import asyncio
import logging
import shutil
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("kinobot")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))
MAX_SECONDS = int(os.getenv("MAX_SECONDS", "240"))
WORKDIR = Path(os.getenv("WORKDIR", "/tmp/kinobot"))
WORKDIR.mkdir(parents=True, exist_ok=True)

bot = Client(
    "kinobot_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)
user = Client(
    "kinobot_streamer",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)
calls = PyTgCalls(user)

current_file = None
current_chat = None
play_lock = asyncio.Lock()


def allowed(chat_id: int) -> bool:
    return ALLOWED_CHAT_ID == 0 or chat_id == ALLOWED_CHAT_ID


def controls():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
            InlineKeyboardButton("▶️ Davom", callback_data="resume"),
        ],
        [
            InlineKeyboardButton("⏹ To‘xtatish", callback_data="stop"),
        ],
    ])


def find_chat_id(message):
    return message.chat.id if message.chat else 0


async def download_video(query: str) -> tuple[str, str]:
    """Download a short video using yt-dlp. Returns (file_path, title)."""
    output = str(WORKDIR / "%(id)s.%(ext)s")
    opts = {
        "format": "best[height<=480][ext=mp4]/best[height<=480]/best",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "match_filter": lambda info, *, incomplete: (
            "Video is longer than the configured limit"
            if info.get("duration") and info["duration"] > MAX_SECONDS
            else None
        ),
        "max_filesize": 180 * 1024 * 1024,
        "socket_timeout": 25,
        "retries": 2,
    }

    # Search YouTube when user sends a title; accept a direct URL too.
    target = query.strip()
    if not target.startswith(("https://", "http://")):
        target = "ytsearch1:" + target

    def work():
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target, download=True)
            if info.get("entries"):
                info = next((x for x in info["entries"] if x), None)
            if not info:
                raise RuntimeError("Video topilmadi.")
            if info.get("duration") and info["duration"] > MAX_SECONDS:
                raise RuntimeError(f"Video {MAX_SECONDS} soniyadan uzun.")
            path = ydl.prepare_filename(info)
            # yt-dlp may change the extension during post-processing.
            if not os.path.exists(path):
                stem = os.path.splitext(path)[0]
                candidates = list(WORKDIR.glob(Path(stem).name + ".*"))
                if candidates:
                    path = str(candidates[0])
            if not os.path.exists(path):
                raise RuntimeError("Yuklangan video fayli topilmadi.")
            return path, info.get("title", "Video")

    return await asyncio.to_thread(work)


@bot.on_message(filters.command(["start", "help"]))
async def start_handler(_, message):
    await message.reply_text(
        "🎬 **KinoBot**\n\n"
        "`/play kino nomi` — qisqa videoni topib uzatish\n"
        "`/play https://...` — video havolasini uzatish\n"
        "`/stop` — uzatishni to‘xtatish\n\n"
        "Eslatma: guruhda avval ovozli chat/video chatni qo‘lda boshlang. "
        "Birinchi sinovda 3 daqiqagacha video ishlatiladi.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📖 Qo‘llanma", callback_data="help")
        ]]),
        quote=True,
    )


@bot.on_message(filters.command("play"))
async def play_handler(_, message):
    global current_file, current_chat
    chat_id = find_chat_id(message)
    if not allowed(chat_id):
        await message.reply_text("⛔ Bu bot ushbu guruhda ishlashga ruxsat etilmagan.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Ishlatish: `/play kino nomi` yoki `/play video_havola`")
        return

    async with play_lock:
        status = await message.reply_text("🔎 Video qidirilyapti va yuklanyapti…")
        path = None
        try:
            path, title = await download_video(parts[1])
            await status.edit_text(f"📺 **Tayyor:** {title}\nOvozli chatga uzatish boshlanmoqda…")
            # PyTgCalls joins/streams using the logged-in user account.
            calls.play(chat_id, path)
            current_file = path
            current_chat = chat_id
            await status.edit_text(
                f"▶️ **Hozir ijro etilyapti:** {title}\n"
                f"⏱ Maksimal uzunlik: {MAX_SECONDS} soniya",
                reply_markup=controls(),
            )
        except Exception as exc:
            log.exception("Playback failed")
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            await status.edit_text(
                "❌ Videoni ishga tushirib bo‘lmadi.\n"
                f"Sabab: `{str(exc)[:500]}`\n\n"
                "Tekshiring: guruhda video/ovozli chat faolmi, "
                "akkaunt guruhga qo‘shilganmi va server logida xato bormi."
            )


@bot.on_message(filters.command("stop"))
async def stop_handler(_, message):
    global current_file, current_chat
    chat_id = find_chat_id(message)
    if not allowed(chat_id):
        return
    try:
        calls.leave_call(chat_id)
    except Exception:
        log.exception("Could not stop call")
    if current_file and os.path.exists(current_file):
        try:
            os.remove(current_file)
        except OSError:
            pass
    current_file = None
    current_chat = None
    await message.reply_text("⏹ Video to‘xtatildi.")


@bot.on_callback_query()
async def callback_handler(_, query):
    global current_file, current_chat
    chat_id = query.message.chat.id if query.message else 0
    if not allowed(chat_id):
        await query.answer("Bu guruhga ruxsat yo‘q.", show_alert=True)
        return

    data = query.data
    try:
        if data == "help":
            await query.answer()
            await query.message.reply_text(
                "Guruhda avval ovozli chatni boshlang, keyin `/play kino nomi` yozing."
            )
        elif data == "pause":
            calls.pause_stream(chat_id)
            await query.answer("Pauza")
        elif data == "resume":
            calls.resume_stream(chat_id)
            await query.answer("Davom etmoqda")
        elif data == "stop":
            calls.leave_call(chat_id)
            if current_file and os.path.exists(current_file):
                try:
                    os.remove(current_file)
                except OSError:
                    pass
            current_file = None
            current_chat = None
            await query.answer("To‘xtatildi")
            await query.message.edit_text("⏹ Video to‘xtatildi.")
        else:
            await query.answer()
    except Exception as exc:
        log.exception("Button action failed")
        await query.answer(f"Xato: {str(exc)[:150]}", show_alert=True)


async def main():
    log.info("Starting bot and user streaming client")
    await bot.start()
    await user.start()
    calls.start()
    me = await user.get_me()
    log.info("Streamer account logged in: %s (%s)", me.first_name, me.id)
    log.info("Bot is running")
    # Keep the worker alive while Pyrogram receives updates.
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
