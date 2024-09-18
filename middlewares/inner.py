import logging
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message
from typing import Any, Callable, Dict, Awaitable
from aiogram.types import TelegramObject
from aiogram_dialog import Dialog, Window, setup_dialogs, DialogManager, Data

from utils.utils import connect_to_db

logger = logging.getLogger(__name__)

class TriggerEventMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__)
   
        result = await handler(event, data)
        return result

class CallbackMiddleware(BaseMiddleware):
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
        return result

class AdminMiddleware(BaseMiddleware):
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
        return result
'''
class DefaultMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug(
            'Вошли в миддлварь %s, тип события %s',
            __class__.__name__,
            event.__class__.__name__,
        )
        user = data["event_from_user"]
        user_id = user.id
        data_to_extract = {
            "phone_number": "<N/A>"
        }
        entities = event.entities or []
        for item in entities:
            if item.type in data_to_extract.keys():
                data_to_extract[item.type] = item.extract_from(event.text)
                phone_number = f'{html.quote(data_to_extract["phone_number"])}'
                if phone_number is not None:
                    user = data["event_from_user"]
                    user_id = user.id
                    conn = connect_to_db()
                    cursor = conn.cursor()

                    cursor.execute(
                        "UPDATE session_store SET phone_number = %s WHERE user_id = %s", (phone_number, user_id)
                    )
                    conn.commit()
        result = await handler(event, data)
        return result
'''