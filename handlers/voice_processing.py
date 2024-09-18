import os
import asyncio
import logging
import uuid

from aiogram import F, Router, Bot, flags
from aiogram.filters import Command, CommandObject, CommandStart 
from aiogram.types import Message
from filters.filters import KeywordFilter
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message, FSInputFile
from utils.utils import save_voice_as_mp3, audio_to_text, voice_processing, connect_to_db

from modules.chain_definition import conversational_rag_chain
from context_vault.context_vault import BOT_REPLIES
from utils.utils import get_images_from_directory

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)

# Инициализируем роутер уровня модуля
voice_router = Router()

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-1'])) 
async def message_with_barnaul_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-1'])
        #await asyncio.sleep(3)
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(5)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/barnaul/"
        album_builder = MediaGroupBuilder(caption="Вот, что у меня нашлось по этом поводу!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-2']))
async def message_with_profinterna_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-2'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/profinterna/"
        album_builder = MediaGroupBuilder(caption="Собрала для вас несколько подходящих фотографий!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-3']))
async def message_with_lenina_27_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-3'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/lenina-27/"
        album_builder = MediaGroupBuilder(caption="Может подойти!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-4']))
async def message_with_kalinina_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-4'])
    await asyncio.sleep(3)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/kalinina/"
        album_builder = MediaGroupBuilder(caption="Готово!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-5']))
async def message_with_lenina_54_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(2)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-5'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/lenina-54/"
        album_builder = MediaGroupBuilder(caption="Вот несколько снимков, которые, на мой взгляд, подойдут!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message((F.text.lower().in_({'едини', 'зови', 'звать'})) & (F.text.contains('админ')))
async def call_admin(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(2)
        await message.reply(BOT_REPLIES['admin-number'])

@voice_router.message(F.content_type == "voice")
async def voice_processing(message: Message, bot: Bot, text: str = None):
     async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
         #await asyncio.sleep(4)
         user_id = message.from_user.id
         conn = connect_to_db()
         cursor = conn.cursor()
         cursor.execute("SELECT session_id FROM session_store WHERE user_id = %s", (user_id,))
         data_extracted = cursor.fetchone()
         session_id = data_extracted["session_id"]

     	 # text is a transcribed_message
         # data["text"] = transcribed_message (in outer.py)
         if text is None:
            text = message.text
         formatted_prompt = (
         "Голосовое сообщение: "
         f"{text}")
         #await message.answer(formatted_prompt)
         bot_response = conversational_rag_chain.invoke({"input": formatted_prompt}, config={"configurable": {"session_id": session_id}})
         bot_answer = bot_response['answer']
         await message.answer(bot_answer)