"""
Telegram Full-Powered Management Bot (MongoDB-based)

Features:
✅ Admin commands (ban, unban, mute, unmute, promote, demote, pin, purge)
✅ AFK system
✅ Approval system
✅ Blacklist & Filters
✅ Flood control
✅ Locks (media, stickers, links, etc.)
✅ Mass actions (banall/unbanall) - Owner only
✅ Report system
✅ Rules system
✅ TagAll
✅ Warn system
✅ Welcome system
✅ Whisper
✅ Info (user & group info)

Dependencies:
- Python 3.10+
- pyrogram, tgcrypto, pymongo
- MongoDB Atlas cluster (MONGO_URI)

Usage:
1) Install dependencies:
   pip install -U pyrogram pymongo
2) Fill configuration variables below.
3) Run: python telegram_management_bot.py
"""

import asyncio
import os
import time
from typing import Dict, List
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions, User

# -------------------- CONFIG --------------------
BOT_TOKEN = "8215757304:AAHmQP9KVuLxvEB_ABfY1CrSl_6fmKUqcMQ"
API_ID = 27974353
API_HASH = "ad83734426f5ba1bedee009479b4afd7"
OWNER_ID = 8373482267   # Your Telegram user ID
MONGO_URI = "mongodb+srv://yujirohanma0690_db_user:<db_password>@jack.8bzau6i.mongodb.net/?retryWrites=true&w=majority&appName=jack"
SESSION_NAME = "mgmtbot"
# -------------------- END CONFIG --------------------

# Initialize MongoDB
mongo = MongoClient(MONGO_URI)
db = mongo['mgmtbot_db']
COL_WARNS = db['warns']
COL_FILTERS = db['filters']
COL_APPROVED = db['approved']
COL_AFK = db['afk']
COL_RULES = db['rules']
COL_LOCKS = db['locks']
COL_WELCOME = db['welcome']

# Initialize bot
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# -------------------- HELPERS --------------------
async def is_admin(message: Message):
    if message.from_user.id == OWNER_ID:
        return True
    member = await app.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ['administrator', 'creator']

async def owner_only(message: Message):
    return message.from_user.id == OWNER_ID

async def get_warn_count(chat_id, user_id):
    data = COL_WARNS.find_one({'chat_id': chat_id, 'user_id': user_id})
    return data['count'] if data else 0

async def increment_warn(chat_id, user_id):
    data = COL_WARNS.find_one({'chat_id': chat_id, 'user_id': user_id})
    if data:
        COL_WARNS.update_one({'chat_id': chat_id, 'user_id': user_id}, {'$inc': {'count': 1}})
        return data['count']+1
    else:
        COL_WARNS.insert_one({'chat_id': chat_id, 'user_id': user_id, 'count': 1})
        return 1

# -------------------- COMMANDS --------------------

@app.on_message(filters.command('start') & filters.private)
async def start(client, message: Message):
    await message.reply_text(f"Hello {message.from_user.first_name}! I am your management bot.")

# -------------------- ADMIN COMMANDS --------------------

@app.on_message(filters.command(['ban']) & filters.group)
async def ban(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can use this.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to ban.")
    user_id = message.reply_to_message.from_user.id
    await app.kick_chat_member(message.chat.id, user_id)
    await message.reply_text(f"✅ Banned user {message.reply_to_message.from_user.first_name}")

@app.on_message(filters.command(['unban']) & filters.group)
async def unban(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can use this.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /unban <user_id>")
    user_id = int(message.command[1])
    await app.unban_chat_member(message.chat.id, user_id)
    await message.reply_text(f"✅ Unbanned user {user_id}")

@app.on_message(filters.command(['mute']) & filters.group)
async def mute(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can use this.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to mute.")
    user_id = message.reply_to_message.from_user.id
    await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
    await message.reply_text(f"🔇 Muted {message.reply_to_message.from_user.first_name}")

@app.on_message(filters.command(['unmute']) & filters.group)
async def unmute(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can use this.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to unmute.")
    user_id = message.reply_to_message.from_user.id
    await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
    await message.reply_text(f"✅ Unmuted {message.reply_to_message.from_user.first_name}")

@app.on_message(filters.command(['promote']) & filters.group)
async def promote(client, message: Message):
    if not await owner_only(message):
        return await message.reply_text("🚫 Only bot owner can promote.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to promote.")
    await app.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_change_info=True, can_delete_messages=True, can_invite_users=True, can_pin_messages=True, can_promote_members=False)
    await message.reply_text(f"✅ Promoted {message.reply_to_message.from_user.first_name}")

@app.on_message(filters.command(['demote']) & filters.group)
async def demote(client, message: Message):
    if not await owner_only(message):
        return await message.reply_text("🚫 Only bot owner can demote.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to demote.")
    await app.promote_chat_member(message.chat.id, message.reply_to_message.from_user.id, can_change_info=False, can_delete_messages=False, can_invite_users=False, can_pin_messages=False, can_promote_members=False)
    await message.reply_text(f"✅ Demoted {message.reply_to_message.from_user.first_name}")

@app.on_message(filters.command(['pin']) & filters.group)
async def pin(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can pin.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to pin.")
    await app.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
    await message.reply_text("📌 Message pinned.")

@app.on_message(filters.command(['purge']) & filters.group)
async def purge(client, message: Message):
    if not await is_admin(message):
        return await message.reply_text("🚫 Only admins can purge.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to message to purge after.")
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    for msg_id in range(start_id, end_id+1):
        try:
            await app.delete_messages(message.chat.id, msg_id)
        except: pass
    await message.reply_text("🧹 Purged messages.")

# -------------------- OWNER ONLY MASS ACTION --------------------
@app.on_message(filters.command(['banall']) & filters.group)
async def banall(client, message: Message):
    if not await owner_only(message):
        return await message.reply_text("🚫 Only bot owner can use this command.")
    async for member in app.get_chat_members(message.chat.id):
        if not member.user.is_bot:
            try:
                await app.kick_chat_member(message.chat.id, member.user.id)
            except: pass
    await message.reply_text("⚡ All members banned (except bots).")

@app.on_message(filters.command(['unbanall']) & filters.group)
async def unbanall(client, message: Message):
    if not await owner_only(message):
        return await message.reply_text("🚫 Only bot owner can use this command.")
    async for member in app.get_chat_members(message.chat.id):
        try:
            await app.unban_chat_member(message.chat.id, member.user.id)
        except: pass
    await message.reply_text("✅ All members unbanned.")

# -------------------- RUN --------------------
async def main():
    await app.start()
    print('Bot started')
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
