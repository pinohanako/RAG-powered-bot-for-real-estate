import logging
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, Message
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)

class KeywordFilter(BaseFilter):
    def __init__(self, keywords: list):
        self.keywords = keywords
   
    # text is a transcribed_message
    # data["text"] = transcribed_message (in outer.py)
    async def __call__(self, message: Message, text: str = None) -> bool:
        logger.debug('Got inside %s', self.__class__.__name__)
        if text is None:
            # If no transcribed text is passed, use a message text
            text = message.text
        contains_all_keywords = all(keyword in text.lower() for keyword in self.keywords)
        if contains_all_keywords:
            return True
        else:
            return False

class TrueFilter(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        logger.debug('Got inside %s', __class__.__name__)
        return True

class HasPhoneNumberFilter(BaseFilter):
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        entities = message.entities or []

        found_phome_numbers = [
            item.extract_from(message.text) for item in entities
            if item.type == "phone_number"
        ]

        if len(found_phome_numbers) > 0:
            return {"phone_numbers": found_phome_numbers}
        return False 