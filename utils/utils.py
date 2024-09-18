import os
import re
import pytz
import io
import pydub
import requests
import uuid
import logging
import psycopg2
import soundfile as sf
import speech_recognition as sr

from os import getenv
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from aiogram.types import ( 
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton)

from pydub import AudioSegment
from typing import Any, Awaitable, Callable, Dict
from aiogram import F, Router, Bot, flags
from aiogram.types import (
    CallbackQuery,
    Message,
    Voice,
    User
)
from aiogram.utils.chat_action import ChatActionSender
from datetime import datetime

from aiogram_dialog.widgets.text import List, Format
from aiogram_dialog import (
    Dialog, DialogManager, setup_dialogs, StartMode, Window
)
from aiogram_dialog.widgets.kbd import Url

from aiogram_dialog import Dialog, Window, setup_dialogs, DialogManager, Data
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Checkbox, Button, Url, Back, Row, Cancel, Start

logger = logging.getLogger(__name__)

def get_now_time():
    now = datetime.now(pytz.timezone('Europe/Moscow'))
    return now.replace(tzinfo=None)

def get_refer_id(command_args):
    try:
        return int(command_args)
    except (TypeError, ValueError):
        return None

def get_images_from_directory(directory_path):
    images = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.jpeg')):
            images.append(os.path.join(directory_path, filename))
    return images

async def save_voice_as_mp3(bot: Bot, voice: Voice) -> str:
    file_id = voice.file_id
    file_info = await bot.get_file(file_id)
    voice_ogg = io.BytesIO()
    await bot.download_file(file_info.file_path, voice_ogg)

    voice_files_dir = "/home/pino/perseus_chat/var/data/voice_files/"
    voice_wav_path = f"{voice_files_dir}/voice-{voice.file_unique_id}.wav"
    AudioSegment.from_file(voice_ogg, format="ogg").export(voice_wav_path, format="wav")
    return voice_wav_path

async def audio_to_text(audio_path: str) -> str:
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
        audio_text = r.recognize_google(audio, language="ru-RU")
    return audio_text

async def voice_processing(message: Message, bot: Bot):
     try:
          async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
              chat_id = message.chat.id
              voice_path = await save_voice_as_mp3(bot, message.voice)
              transcribed_voice_text = await audio_to_text(voice_path)
              logger.debug(f'Transcribed voice message: {transcribed_voice_text}')
              return transcribed_voice_text
     except:
     	  await message.reply(text="Извините, не удалось распознать сообщение\nПопробуйте устранить акустические и артикуляторные помехи")

def float_to_str(float_number):
    if int(float_number) == float_number:
        return str(int(float_number))
    else:
        return str(float_number)

def price_float_value(string_value):
    if not string_value:
        return ""
    else:
        return float(string_value)

def connect_to_db():
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB_IP = os.getenv("POSTGRES_DB_IP")
    conn_info = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_DB_IP}:5432/messages"
    conn = psycopg2.connect(conn_info, cursor_factory=RealDictCursor)
    return conn

ADMINS = os.getenv("ADMINS")

def get_all_users(table_name='session_store', count=False):
    conn = connect_to_db()
    cursor = conn.cursor()

    admins = [int(admin_id) for admin_id in ADMINS.split(',')]
    cursor.execute("SELECT full_name, user_id, created_at, phone_number, selected_address, selected_guests, selected_age, check_in_date, check_out_date FROM session_store")
    all_users_data = cursor.fetchall()

    if count:
        return len(all_users_data)
    else:
        return all_users_data

def home_page_kb(user_telegram_id: int):
    admins = [int(admin_id) for admin_id in ADMINS.split(',')]
    kb_list = [[KeyboardButton(text="🔙 Назад")]]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )

def check_database_updates():
    all_users = get_all_users()
    for user in all_users:
        user_id = user[1]
        full_name = user[0]
        send_admin_notification(user_id, full_name)
'''
@trigger_router.message((F.text.lower().in_({'едини', 'зови', 'звать'})) & (F.text.contains('админ')))
async def call_admin(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        admins = [int(admin_id) for admin_id in ADMINS.split(',')]
        all_users_data = get_all_users()
        full_name = message.from_user.full_name
        user_id = message.from_user.id
        bot_key = os.getenv("NOTIFICATION_BOT_TOKEN")
        text = f'Пользователь по имени {full_name} хочет связаться!\n\n Телеграм ID: {user_id}'
        for user in all_users_data:
            if user.get("phone_number") is not None:
                text += f'😱 Номер: {user.get("phone_number")} 😱\n'

            if user.get("selected_address") is not None:
                text += f'🔑 Адрес: {user.get("selected_address")}\n'

            if user.get("refer_id") is not None:
                text += f'🤮 Количество гостей: {user.get("selected_guests")}\n'

            if user.get("selected_age") is not None:
                text += f'🤦 Возраст: {user.get("selected_age")}\n'

            if user.get("check_in_date") is not None:
                text += f'💩 Когда заезд: {user.get("check_in_date")}\n'

            if user.get("check_out_date") is not None:
                text += f'💩 Когда выезд: {user.get("check_out_date")}\n'

        for chat_id in admins:

            send_message_url = f'https://api.telegram.org/bot{bot_key}/sendMessage?chat_id={chat_id}&text={text}'
            requests.post(send_message_url)
            #await bot.send_message(chat_id=chat_id, text=f'Пользователь по имени {full_name} хочет связаться!\n\n user_id: {user_id}')
        await message.answer("Отправила уведомление! Если хотите получить обратную связь быстрее, ниже представлен номер")
        await bot.send_contact(chat_id=message.chat.id, phone_number=BOT_REPLIES['number_value'], first_name="Елена")
'''