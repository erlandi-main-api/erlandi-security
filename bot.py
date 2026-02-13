import os
from typing import Optional, Set

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# =========================
# CONFIG
# =========================
BOT_NAME = "🛡️ Erlandi Security"
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set via .env / export
FBAN_FILE = "data/fban.txt"

# (Opsional) isi user_id kamu kalau mau jadi super admin
SUDO_ADMINS = set([
    # 123456789,
])

WELCOME_TEXT = (
    "{bot}\n"
    "━━━━━━━━━━━━━━\n"
    "🎉 Selamat datang {mention} di *{chat_title}*\n"
    "━━━━━━━━━━━━━━"
)

# =========================
# FBAN TXT STORAGE (Opsi 2)
# =========================
def load_fban() -> Set[int]:
    s = set()
    if not os.path.exists(FBAN_FILE):
        return s
    with open(FBAN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                s.add(int(line))
    return s

def save_fban(fbans: Set[int]) -> None:
    os.makedirs(os.path.dirname(FBAN_FILE), exist_ok=True)
    with open(FBAN_FILE, "w", encoding="utf-8") as f:
        for uid in sorted(fbans):
            f.write(f"{uid}\n")

FBANS: Set[int] = load_fban()

def fban_add(user_id: int):
    FBANS.add(user_id)
    save_fban(FBANS)

def fban_remove(user_id: int):
    FBANS.discard(user_id)
    save_fban(FBANS)

def fban_check(user_id: int) -> bool:
    return user_id in FBANS

# =========================
# HELPERS
# =========================
def get_target_user_id(update: Update) -> Optional[int]:
    """Ambil target dari reply atau /cmd <user_id>"""
    msg = update.effective_message
    if msg and msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id

    if msg and msg.text:
        parts = msg.text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
    return None

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if user.id in SUDO_ADMINS:
        return True

    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

async def require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_admin(update, context):
        await update.effective_message.reply_text(f"{BOT_NAME}\n❌ Perintah ini hanya untuk admin.")
        return False
    return True

def mention_html(user) -> str:
    # safe mention HTML
    name = (user.full_name or "user").replace("<", "").replace(">", "")
    return f"<a href='tg://user?id={user.id}'>{name}</a>"

# =========================
# COMMANDS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"{BOT_NAME}\n"
        "Bot admin mini aktif.\n\n"
        "Commands:\n"
        "/kick (reply)\n"
        "/ban (reply)\n"
        "/unban <user_id>\n"
        "/fban (reply)\n"
        "/unfban <user_id>\n"
        "/promote (reply)\n"
    )

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    chat = update.effective_chat
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan reply atau: /kick <user_id>")

    try:
        # Kick = ban lalu unban
        await context.bot.ban_chat_member(chat.id, target)
        await context.bot.unban_chat_member(chat.id, target)

        await update.effective_message.reply_text(
            f"{BOT_NAME}\n━━━━━━━━━━━━━━\n✅ *Action:* KICK\n🆔 *Target:* `{target}`\n━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"{BOT_NAME}\n❌ Gagal kick: {e}")

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    chat = update.effective_chat
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan reply atau: /ban <user_id>")

    try:
        await context.bot.ban_chat_member(chat.id, target)
        await update.effective_message.reply_text(
            f"{BOT_NAME}\n━━━━━━━━━━━━━━\n🚫 *Action:* BAN\n🆔 *Target:* `{target}`\n━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"{BOT_NAME}\n❌ Gagal ban: {e}")

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    chat = update.effective_chat
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan: /unban <user_id>")

    try:
        await context.bot.unban_chat_member(chat.id, target)
        await update.effective_message.reply_text(
            f"{BOT_NAME}\n━━━━━━━━━━━━━━\n✅ *Action:* UNBAN\n🆔 *Target:* `{target}`\n━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"{BOT_NAME}\n❌ Gagal unban: {e}")

async def cmd_fban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    chat = update.effective_chat
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan reply atau: /fban <user_id>")

    fban_add(target)

    # Optional: langsung ban di chat ini juga
    try:
        await context.bot.ban_chat_member(chat.id, target)
    except:
        pass

    await update.effective_message.reply_text(
        f"{BOT_NAME}\n━━━━━━━━━━━━━━\n⛔ *Action:* FBAN\n🆔 *Target:* `{target}`\n📌 *Status:* Ditambahkan ke daftar global\n━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_unfban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan: /unfban <user_id>")

    fban_remove(target)
    await update.effective_message.reply_text(
        f"{BOT_NAME}\n━━━━━━━━━━━━━━\n✅ *Action:* UNFBAN\n🆔 *Target:* `{target}`\n━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context): return
    chat = update.effective_chat
    target = get_target_user_id(update)
    if not target:
        return await update.effective_message.reply_text(f"{BOT_NAME}\nGunakan reply atau: /promote <user_id>")

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_promote_members=False,
        )
        await update.effective_message.reply_text(
            f"{BOT_NAME}\n━━━━━━━━━━━━━━\n👑 *Action:* PROMOTE\n🆔 *Target:* `{target}`\n━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"{BOT_NAME}\n❌ Gagal promote: {e}")

# =========================
# WELCOME + AUTO FBAN ON JOIN
# =========================
async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    for user in msg.new_chat_members:
        # Auto FBan
        if fban_check(user.id):
            try:
                await context.bot.ban_chat_member(chat.id, user.id)
                await msg.reply_text(
                    f"{BOT_NAME}\n━━━━━━━━━━━━━━\n🚫 FBAN Detected\n👤 {mention_html(user)}\n✅ Auto-banned\n━━━━━━━━━━━━━━",
                    parse_mode="HTML"
                )
            except Exception as e:
                await msg.reply_text(f"{BOT_NAME}\nFBan terdeteksi tapi gagal ban: {e}")
            continue

        # Welcome
        try:
            await msg.reply_text(
                WELCOME_TEXT.format(
                    bot=BOT_NAME,
                    mention=user.full_name,
                    chat_title=(chat.title or "grup ini")
                ),
                parse_mode="Markdown"
            )
        except Exception:
            await msg.reply_text(f"{BOT_NAME}\n🎉 Selamat datang {user.full_name}!")

# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diset. Jalankan: export BOT_TOKEN='xxxxx'")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("fban", cmd_fban))
    app.add_handler(CommandHandler("unfban", cmd_unfban))
    app.add_handler(CommandHandler("promote", cmd_promote))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))

    app.run_polling()

if __name__ == "__main__":
    main()
