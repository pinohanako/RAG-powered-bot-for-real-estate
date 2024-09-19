import os
import asyncio
import logging
import environ

from os import getenv
from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, types
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram.utils.chat_action import (
    ChatActionMiddleware
)
from middlewares.outer import (
    VoiceTranscriptionMiddleware,
    CallbackOuterMiddleware,
)
from middlewares.inner import (
    TriggerEventMiddleware,
    CallbackMiddleware,
    AdminMiddleware,
)

from handlers.chat import chat_router
from handlers.admin import admin_router
from handlers.trigger import trigger_router
from handlers.voice_processing import voice_router

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] #%(levelname)-8s %(filename)s:'
           '%(lineno)d - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, 
              default=DefaultBotProperties(parse_mode=ParseMode.HTML, 
                                           protect_content=True))
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

    # Administrator access to database content
    admin_router.message.middleware(AdminMiddleware())

    # Middleware for handling all non-trigger messages if filters return False
    chat_router.message.middleware(ChatActionMiddleware())
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

asyncio.run(main(), debug=True)