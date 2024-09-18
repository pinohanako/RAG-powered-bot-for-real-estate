import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import Bot, BaseMiddleware
from aiogram.types import TelegramObject, Message

from aiogram.types import ContentType

from utils.utils import voice_processing, connect_to_db

from os import getenv
from dotenv import load_dotenv

import asyncio
import uuid
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, async_scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
#from databases import Database
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

#from asyncpg_lite import DatabaseManager

logger = logging.getLogger(__name__)

#def connect_to_db():
#    POSTGRES_USER = os.getenv("POSTGRES_USER")
#    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
#    POSTGRES_DB_IP = os.getenv("POSTGRES_DB_IP")
#    conn_info = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_DB_IP}:5432/messages"
#    conn = psycopg2.connect(conn_info, cursor_factory=RealDictCursor)
#    return conn
'''
class VoiceTranscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug(
            'Event type %s',
            event.__class__.__name__
        )
        # Checking if a voice message
        if event.content_type == ContentType.VOICE:
            bot = data["bot"]
            transcribed_message = await voice_processing(event, bot)
            data["text"] = transcribed_message
            result = await handler(event, data)
            logger.debug('leaving %s with a transcription', __class__.__name__)
            return result
        else:
            result = await handler(event, data)
            logger.debug('leaving %s with an original text', __class__.__name__)
            return result
'''



class VoiceTranscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event:  Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug(
            'Event type %s',
            event.__class__.__name__
        )
        if event.content_type == ContentType.VOICE:
            bot = data["bot"]
            transcribed_message = await voice_processing(event, bot)
            data["text"] = transcribed_message

            user = data["event_from_user"]
            full_name = user.full_name
            user_id = user.id
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, full_name FROM session_store WHERE user_id = %s", (user_id,))
            data_extracted = cursor.fetchone()

            data["session_id"] = data_extracted["session_id"]
            data["full_name"] = data_extracted["full_name"]
            result = await handler(event, data)
            #cursor.execute("UPDATE message_store AS ms SET message = jsonb_set(ms.message, '{data, id}', to_jsonb(%s), true) FROM session_store AS ss WHERE ms.session_id = ss.session_id::uuid")
            #cursor.execute("UPDATE message_store AS ms SET message = jsonb_set(ms.message, '{data, name}', to_jsonb(%s), true) FROM session_store AS ss WHERE ms.session_id = ss.session_id::uuid")
            logger.debug('leaving %s with a transcription', __class__.__name__)
            return result
        else:
            user = data["event_from_user"]
            full_name = user.full_name
            user_id = user.id
            conn = connect_to_db()
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, full_name FROM session_store WHERE user_id = %s", (user_id,))
            data_extracted = cursor.fetchone()
            if data_extracted:
                 data["session_id"] = data_extracted["session_id"]
                 data["full_name"] = data_extracted["full_name"]
                 result = await handler(event, data)
                 logger.debug('Extracted data from postgres!')
                 logger.debug('Leaving %s with an original text', __class__.__name__)
                 return result
            else:
                 session_id = str(uuid.uuid4())
                 data["session_id"] = session_id
                 cursor.execute("INSERT INTO session_store (user_id, session_id, full_name) VALUES (%s, %s, %s)", (user_id, session_id, full_name))
                 conn.commit()
                 logger.debug('Data are inserted into postgres = we have a new user!')
                 result = await handler(event, data)

                 logger.debug('Leaving %s with an original text', __class__.__name__)
                 return result
            
class CallbackOuterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )
        user = data["event_from_user"]
        full_name = user.full_name
        user_id = user.id
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, full_name FROM session_store WHERE user_id = %s", (user_id,))
        data_extracted = cursor.fetchone()
        if data_extracted:
            data["session_id"] = data_extracted["session_id"]
            data["full_name"] = data_extracted["full_name"]
            result = await handler(event, data)
            return result
        else:
            session_id = str(uuid.uuid4())
            data["session_id"] = session_id
            cursor.execute("INSERT INTO session_store (user_id, session_id, full_name) VALUES (%s, %s, %s)", (user_id, session_id, full_name))
            conn.commit()
            logger.debug('Data are inserted into postgres = we have a new user!')
            result = await handler(event, data)
            return result

class ThirdOuterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__
        )
        result = await handler(event, data)
        logger.debug('Выходим из миддлвари  %s', __class__.__name__)

        return result
