import logging
import random
import asyncio
import uuid
from enum import Enum

from typing import Any, Dict
from aiogram import F, Router, Bot, flags
from aiogram.types import Message, Voice

from aiogram.utils.chat_action import ChatActionSender
from modules.chain_definition import conversational_rag_chain
from context_vault.context_vault import BOT_REPLIES
from utils.utils import connect_to_db
from filters.filters import TrueFilter

logger = logging.getLogger(__name__)

chat_router = Router()

@chat_router.message(F.text)
async def any_text(message: Message, bot: Bot, session_id: str = None):
     async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
         await asyncio.sleep(2)
         user_id = message.from_user.id
         conn = connect_to_db()
         cursor = conn.cursor()
         cursor.execute("SELECT session_id FROM session_store WHERE user_id = %s", (user_id,))
         data_extracted = cursor.fetchone()
         session_id = data_extracted["session_id"]
         text = message.text

         bot_response = conversational_rag_chain.invoke({"input": text}, config={"configurable": {"session_id": session_id}})
         #await asyncio.sleep(6)
         bot_answer = bot_response['answer']
         await message.answer(bot_answer)

@chat_router.message(F.photo)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def photo_msg(message: Message):
    chat_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("SELECT used_photo_phrases FROM session_store WHERE user_id = %s", (chat_id,))
    data_extracted = cursor.fetchone()
    if data_extracted["used_photo_phrases"] is None:
        used_phrases_photo = []
    else:
        used_phrases_photo = f"{data_extracted['used_photo_phrases']}"

    funny_photo_phrases: List[str] = BOT_REPLIES["funny-photo-phrases"]

    if len(used_phrases_photo) < len(funny_photo_phrases):
        unused_phrases = [
            phrase for phrase in funny_photo_phrases if phrase not in used_phrases_photo
        ]
        random_phrase = random.choice(unused_phrases)
        used_phrases_photo.append(random_phrase)
        selected_photo_phrases = {"photo_phrases": used_phrases_photo}
        used_phrases_photo_value = f"{selected_photo_phrases['photo_phrases']}"

        await asyncio.sleep(5)
        cursor.execute(
            "UPDATE session_store SET used_photo_phrases = %s WHERE user_id = %s",
            (used_phrases_photo_value, chat_id),
        )
        conn.commit()
        await message.answer(random_phrase)
    else:
        await asyncio.sleep(3)
        await message.answer(
            f"{message.from_user.full_name}, спасибо за то, что продолжаете делиться со мной изображениями. Но, может быть, нам пора поговорить? Я достаточно намекнула, что работаю только с данными естественного языка."
        )
    conn.close()

@chat_router.message(F.sticker)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def sticker(message: Message):
    chat_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("SELECT used_sticker_phrases FROM session_store WHERE user_id = %s", (chat_id,))
    data_extracted = cursor.fetchone()
    if data_extracted["used_sticker_phrases"] is None:
        used_phrases_stickers = []
    else:
        used_phrases_stickers = data_extracted["used_sticker_phrases"]  # Извлекаем список фраз
    
    funny_phrases: List[str] = BOT_REPLIES['funny-phrases']
    if len(used_phrases_stickers) < len(funny_phrases):
        unused_phrases = [phrase for phrase in funny_phrases if phrase not in used_phrases_stickers]
        random_phrase = random.choice(unused_phrases)
        used_phrases_stickers.append(random_phrase)

        await asyncio.sleep(5)
        cursor.execute("UPDATE session_store SET used_sticker_phrases = %s WHERE user_id = %s", (used_phrases_stickers, chat_id))
        conn.commit()
        await message.answer(random_phrase)
    else:
        await asyncio.sleep(3)
        await message.answer(f"Спасибо, {message.from_user.full_name}, но я устала намекать, что мне это не нравится!\nНам пора поговорить?")
    conn.close()

# This handler will be triggered on any messages,
# except those for which there are separate handlers
@chat_router.message(TrueFilter())
async def send_echo(message: Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.reply(text=BOT_REPLIES['no_echo']) 