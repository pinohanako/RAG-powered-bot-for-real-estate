import os
import asyncio
import logging

from aiogram import F, Router, Bot
from aiogram.types import Message
from filters.filters import KeywordFilter
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message, FSInputFile

from modules.chain_definition import conversational_rag_chain
from utils.utils import voice_processing, connect_to_db, get_images_from_directory
from context_vault.context_vault import BOT_REPLIES

logger = logging.getLogger(__name__)

voice_router = Router()

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-1'])) 
async def message_with_city_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-1'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/city/"
        album_builder = MediaGroupBuilder(caption="Вот, что у меня нашлось по этом поводу!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-2']))
async def message_with_addres_4_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-2'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-4/"
        album_builder = MediaGroupBuilder(caption="Собрала для вас несколько подходящих фотографий!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-3']))
async def message_with_address_2_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-3'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-2/"
        album_builder = MediaGroupBuilder(caption="Может подойти!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-4']))
async def message_with_address_1_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing a transcribed message with keywords: '
            'guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-4'])
    await asyncio.sleep(3)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-1/"
        album_builder = MediaGroupBuilder(caption="Готово!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice", KeywordFilter(BOT_REPLIES['address-keywords-5']))
async def message_with_address_3_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(2)
        logger.debug('Entered handler processing a transcribed message with keywords: '
            'guess about request to send photos')
        await message.reply(BOT_REPLIES['photo-search-5'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-3/"
        album_builder = MediaGroupBuilder(caption="Вот несколько снимков, которые, на мой взгляд, подойдут!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@voice_router.message(F.content_type == "voice")
async def voice_processing(message: Message, bot: Bot, text: str = None):
     chat_id = message.from_user.id
     async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
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
         bot_response = conversational_rag_chain.invoke({"input": formatted_prompt}, 
                                                         config={"configurable": {"session_id": session_id}})
         bot_answer = bot_response['answer']
         await message.answer(bot_answer)