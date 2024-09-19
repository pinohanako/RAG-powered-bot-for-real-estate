import asyncio
import os
from os import getenv
from enum import Enum

from typing import Any, Dict
from aiogram import F, Router, Bot
from aiogram.types import Message

from aiogram.utils.chat_action import ChatActionSender

from context_vault.context_vault import BOT_REPLIES
from utils.utils import (
    get_all_users, 
    connect_to_db, 
    admin_keyboard
)

admin_router = Router()

ADMINS = os.getenv("ADMINS")
admins = [int(admin_id) for admin_id in ADMINS.split(',')]

@admin_router.message((F.text.contains('Панель')) & (F.from_user.id.in_(admins)))
async def get_profile(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        all_users_data = get_all_users()

        text = (
            f'👀 Общее количество человек в базе: <b>{len(all_users_data)}</b>\n\n'
        )
        for user in all_users_data:
            text += (
                f'🤢 Полное имя: {user.get("full_name")}\n'
                f'👤 Телеграм ID: {user.get("user_id")}\n'
                f'⏰ Впервые присоединился: {user.get("created_at")}\n'
            )
            if user.get("phone_number") is not None:
                text += f'😱 Номер: {user.get("phone_number")} 😱\n'

            if user.get("selected_address") is not None:
                text += f'🔑 Адрес: {user.get("selected_address")}\n'

            if user.get("selected_guests") is not None:
                text += f'🤮 Количество гостей: {user.get("selected_guests")}\n'

            if user.get("selected_age") is not None:
                text += f'🤦 Возраст: {user.get("selected_age")}\n'

            if user.get("check_in_date") is not None:
                text += f'💩 Когда заезд: {user.get("check_in_date")}\n'

            if user.get("check_out_date") is not None:
                text += f'💩 Когда выезд: {user.get("check_out_date")}\n'

            text += (f'\n〰️〰️〰️〰️〰️〰️〰️〰️〰️\n\n')

    await message.answer(text, reply_markup=admin_keyboard(message.from_user.id)) 

