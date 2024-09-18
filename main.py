import os
import asyncio
import logging
import environ

from os import getenv

from aiogram import Bot, Dispatcher
from aiogram import types
#from config.config import Config, load_config
from aiogram.enums import ParseMode
from lxml import html
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode 

from handlers.voice_processing import voice_router
from handlers.trigger import trigger_router
from handlers.admin import admin_router

from handlers.chat import chat_router
from aiogram.utils.chat_action import ChatActionMiddleware


from middlewares.outer import (
    VoiceTranscriptionMiddleware,
    CallbackOuterMiddleware,
)
from middlewares.inner import (
    TriggerEventMiddleware,
    CallbackMiddleware,
    AdminMiddleware,
    #DefaultMiddleware,
)
from utils.utils import get_all_users
'''
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import sessionmaker
from sqlalchemy import BigInteger, String, Integer
'''


#from sqlalchemy.engine import URL
#from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, async_scoped_session
#from sqlalchemy import create_engine

'''url_object = URL.create("postgresql+asyncpg", 
                         username="postgres", 
                         password="04idesaf", 
                         host="172.18.0.3", 
                         database="users_reg")'''

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] #%(levelname)-8s %(filename)s:'
           '%(lineno)d - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = os.getenv("ADMINS")

    # Загружаем конфиг в переменную config
    # config: Config = load_config()
    # engine = create_async_engine(url_object, echo=True)
    # session = async_sessionmaker(engine, expire_on_commit=False)
    # from sqlalchemy import Integer, String
    # db_manager = DatabaseManager(db_url="postgresql://postgres:04idesaf@172.18.0.3:5432/users_reg", 
                                 #deletion_password="04idesaf",
                                 #log_level=logging.DEBUG)

async def main() -> None:
    #admins = [int(admin_id) for admin_id in ADMINS.split(',')]

    bot = Bot(token=BOT_TOKEN, #config.tg_bot.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
                                          #protect_content=True)
    dp = Dispatcher()

    dp.include_router(voice_router)
    dp.include_router(trigger_router)
    dp.include_router(admin_router)
    dp.include_router(chat_router)
    
    dp.callback_query.outer_middleware(CallbackOuterMiddleware())

    # Middleware for handling voice messages and making transcription, event type: message
    voice_router.message.outer_middleware(VoiceTranscriptionMiddleware())
    
    # Filters are applied somewhere around here

    # TriggerEventMiddleware for handling all written and transcribed messages when filters return True, event type: message
    trigger_router.message.middleware(TriggerEventMiddleware())
    
    # CallbackMiddleware for providing a callback mechanism to execute custom actions based on specific message types or content, event type: callback_query
    trigger_router.callback_query.middleware(CallbackMiddleware())

    # Administrator access to the database
    admin_router.message.middleware(AdminMiddleware())

    # Middleware for handling all non-trigger messages if filters return False
    chat_router.message.middleware(ChatActionMiddleware())
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

asyncio.run(main(), debug=True)