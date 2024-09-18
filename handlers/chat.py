import logging
import random
import asyncio
import uuid
import aiopg
from enum import Enum

from typing import Any, Dict
from aiogram import F, Router, Bot, flags
from aiogram.types import Message, Voice

from aiogram.utils.chat_action import ChatActionSender
from modules.chain_definition import conversational_rag_chain
from context_vault.context_vault import BOT_REPLIES
from utils.utils import connect_to_db
from filters.filters import MyTrueFilter

logger = logging.getLogger(__name__)

# Инициализируем роутер уровня модуля
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
'''
@chat_router.message(F.photo)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def photo_msg(message: Message):
    user_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()

    # Извлекаем данные из таблицы session_store для конкретного пользователя
    cursor.execute("SELECT COALESCE(used_photo_phrases, '(none)') FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()

    data_extracted_str = str(data_extracted)
    if data_extracted is not None:
        data_extracted_str = str(data_extracted)
        if data_extracted_str is not None:
            used_phrases_photo = data_extracted_str.split(',')  # Разделить строку на список фраз
        else:
            used_phrases_photo = []
    else:
        used_phrases_photo = []

    funny_photo_phrases = BOT_REPLIES['funny-photo-phrases']  # Получаем список забавных фраз для фото

    if len(used_phrases_photo) < len(funny_photo_phrases):
        unused_phrases = [phrase for phrase in funny_photo_phrases if phrase not in used_phrases_photo]
        random_phrase = random.choice(unused_phrases)
        used_phrases_photo.append(random_phrase)
        await message.answer(random_phrase)
        cursor.execute("""
               UPDATE session_store
               SET used_photo_phrases = CASE 
                   WHEN used_photo_phrases IS NULL THEN %s 
                   ELSE array_append(used_photo_phrases, %s) 
               END
               WHERE user_id = %s;
               """, (used_phrases_photo, random_phrase, user_id))
        conn.commit()
    else:
        cursor.execute("SELECT full_name FROM session_store WHERE user_id = %s", (user_id,))
        name_extracted = cursor.fetchone()
        await message.answer(
            f"{name_extracted['full_name']}, спасибо за то, что продолжаете делиться со мной изображениями. Но, может быть, нам пора поговорить? Я достаточно намекнула, что работаю только с данными естественного языка"
        )

@chat_router.message(F.sticker)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def sticker(message: Message):
    user_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(used_sticker_phrases, '(none)') FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()
    
    data_extracted_str = str(data_extracted)
    if data_extracted is not None:
        data_extracted_str = str(data_extracted)
        if data_extracted_str is not None:
           used_phrases_stickers = data_extracted_str.split(',')  # Разделить строку на список фраз
        else:
            used_phrases_stickers = []
    else:
        used_phrases_stickers = []

    funny_phrases = BOT_REPLIES['funny-phrases']  # Получаем список забавных фраз

    if len(used_phrases_stickers) < len(funny_phrases):
        unused_phrases = [phrase for phrase in funny_phrases if phrase not in used_phrases_stickers]
        random_phrase = random.choice(unused_phrases)
        used_phrases_stickers.append(random_phrase)
        await message.answer(random_phrase)
        cursor.execute("""
               UPDATE session_store
               SET used_sticker_phrases = CASE 
                   WHEN used_sticker_phrases IS NULL THEN %s::text[] 
                   ELSE array_append(used_sticker_phrases::text[], %s::text) 
               END
               WHERE user_id = %s;
               """, (used_phrases_stickers, random_phrase, user_id))
        conn.commit()
    else:
        cursor.execute("SELECT full_name FROM session_store WHERE user_id = %s", (user_id,))
        name_extracted = cursor.fetchone()
        await message.answer(f"Спасибо, {name_extracted['full_name']}, но я устала намекать, что мне это не нравится!\nНам пора поговорить?")
'''

'''
@chat_router.message(F.photo)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def photo_msg(message: Message):
    user_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Извлекаем данные из таблицы session_store для конкретного пользователя
    cursor.execute("SELECT COALESCE(used_photo_phrases, '(none)') FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()
    if data_extracted is not None:
        used_phrases_photo = data_extracted
    else:
        used_phrases_photo = []

    funny_photo_phrases: List[str] = BOT_REPLIES['funny-photo-phrases'] 

    if len(used_phrases_photo) < len(funny_photo_phrases):
        unused_phrases = [phrase for phrase in funny_photo_phrases if phrase not in used_phrases_photo]
        random_phrase = random.choice(unused_phrases)
        used_phrases_photo.append(random_phrase)
        await message.answer(random_phrase)
        cursor.execute("""
                      UPDATE session_store
                      SET used_photo_phrases = CASE WHEN used_photo_phrases IS NULL THEN %s ELSE CONCAT(used_photo_phrases, ', ', %s) END
                      WHERE user_id = %s;
                      """, (used_phrases_photo, user_id))
        conn.commit()
    else:
        cursor.execute("SELECT full_name FROM session_store WHERE user_id = %s", (user_id,))
        name_extracted = cursor.fetchone()
        await message.answer(
            f"{name_extracted['full_name']}, спасибо за то, что продолжаете делиться со мной изображениями. Но, может быть, нам пора поговорить? Я достаточно намекнула, что работаю только с данными естественного языка"
        )
'''

used_phrases_photo = {}
async def photo_msg(message: Message):
    user_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT used_photo_phrases FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()
    used_phrases_photo = data_extracted["used_photo_phrases"]

    if chat_id not in used_phrases_photo:
        used_phrases_photo[chat_id] = []

    funny_photo_phrases: List[str] = BOT_REPLIES['funny-photo-phrases'] 

    if len(used_phrases_photo[chat_id]) < len(funny_photo_phrases):
        unused_phrases = [phrase for phrase in funny_photo_phrases if phrase not in used_phrases_photo[chat_id]]
        random_phrase = random.choice(unused_phrases)
        used_phrases_photo[chat_id].append(random_phrase)
        #await asyncio.sleep(5)
        await message.answer(random_phrase)
    else:
        #await asyncio.sleep(3)
        await message.answer(
            f"{message.from_user.full_name}, спасибо за то, что продолжаете делиться со мной изображениями. Но, может быть, нам пора поговорить? Я достаточно намекнула, что работаю только с данными естественного языка"
        )

'''
@chat_router.message(F.sticker)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def sticker(message: Message):
    user_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Извлекаем данные из таблицы session_store для конкретного пользователя
    cursor.execute("SELECT COALESCE(used_sticker_phrases, '(none)') FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()
    if data_extracted is not None:
        used_phrases_stickers = data_extracted
    else:
        used_phrases_stickers = []

    funny_phrases: List[str] = BOT_REPLIES['funny-phrases'] 

    if len(used_phrases_stickers) < len(funny_phrases):
        unused_phrases = [phrase for phrase in funny_phrases if phrase not in used_phrases_stickers]
        random_phrase = random.choice(unused_phrases)
        used_phrases_stickers.append(random_phrase)
        await message.answer(random_phrase)
        cursor.execute("INSERT INTO session_store (used_sticker_phrases) VALUES (%s) WHERE user_id = %s", (used_phrases_stickers, user_id))
        conn.commit()
    else:
        cursor.execute("SELECT full_name FROM session_store WHERE user_id = %s", (user_id,))
        name_extracted = cursor.fetchone()
        await message.answer(
            await message.answer(f"Спасибо, {name_extracted['full_name']}, но я устала намекать, что мне это не нравится!\nНам пора поговорить?")
        )
'''

async def connect_to_db2():
    db_connection = await aiopg.connect(
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_DB_IP"),
        port="5432",
        dbname="messages"
    )
    return db_connection

@chat_router.message(F.sticker)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def sticker(message: Message):
    chat_id = message.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()

    await cursor.execute("SELECT used_sticker_phrases FROM session_store WHERE user_id = %s", (chat_id,))
    data_extracted = await cursor.fetchone()
    used_phrases_stickers = data_extracted["used_sticker_phrases"] if data_extracted else []

    if chat_id not in used_phrases_stickers:
        used_phrases_stickers[chat_id] = []

    funny_phrases: List[str] = BOT_REPLIES['funny-phrases']
    if len(used_phrases_stickers[chat_id]) < len(funny_phrases):
        unused_phrases = [phrase for phrase in funny_phrases if phrase not in used_phrases_stickers[chat_id]]
        random_phrase = random.choice(unused_phrases)
        used_phrases_stickers[chat_id].append(random_phrase)
        await asyncio.sleep(5)
        await cursor.execute("UPDATE session_store SET used_sticker_phrases = %s WHERE user_id = %s", (used_phrases_stickers, chat_id))
        await conn.commit()
        await message.answer(random_phrase)
    else:
        await asyncio.sleep(3)
        await message.answer(f"Спасибо, {message.from_user.full_name}, но я устала намекать, что мне это не нравится!\nНам пора поговорить?")

    # Обновление списка использованных фраз в базе данных
    #await cursor.execute("UPDATE session_store SET used_sticker_phrases = %s WHERE user_id = %s", (used_phrases_stickers, chat_id))
    #await conn.commit()
    await conn.close()

#################### работает ниже
'''
used_phrases_stickers = {}
@chat_router.message(F.sticker)
@flags.chat_action(initial_sleep=2, action="typing", interval=3)
async def sticker(message: Message):
     chat_id = message.from_user.id
    # conn = connect_to_db()
     #cursor = conn.cursor()
     #cursor.execute("SELECT used_sticker_phrases FROM session_store WHERE user_id = %s", (user_id,))
     #data_extracted = cursor.fetchone()
     #used_phrases_stickers = data_extracted["used_sticker_phrases"]

     if chat_id not in used_phrases_stickers:
          used_phrases_stickers[chat_id] = []

     funny_phrases: List[str] = BOT_REPLIES['funny-phrases']
     if len(used_phrases_stickers[chat_id]) < len(funny_phrases):
          unused_phrases = [phrase for phrase in funny_phrases if phrase not in used_phrases_stickers[chat_id]]
          random_phrase = random.choice(unused_phrases)
          used_phrases_stickers[chat_id].append(random_phrase)
          #await asyncio.sleep(5)
          await message.answer(random_phrase)
     else:
          #c asyncio.sleep(3)
          await message.answer(f"Спасибо, {message.from_user.full_name}, но я устала намекать, что мне это не нравится!\nНам пора поговорить?")
'''
# This handler will be triggered on any messages,
# except those for which there are separate handlers
@chat_router.message(MyTrueFilter())
async def send_echo(message: Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.reply(text=BOT_REPLIES['no_echo'])