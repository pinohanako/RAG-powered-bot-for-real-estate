
import uuid
import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import Bot, BaseMiddleware
from aiogram.types import TelegramObject, Message, ContentType

from utils.utils import voice_processing, connect_to_db

logger = logging.getLogger(__name__)

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
            logger.debug('Leaving %s with a transcription', __class__.__name__)
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
                 logger.debug('The insertion of data into database signifies the arrival of a NEW USER!')
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
            'Event type %s',
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
            logger.debug('The insertion of data into database signifies the arrival of a NEW USER!')
            result = await handler(event, data)
            return result
