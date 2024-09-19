import os
import re
import io
import pydub
import requests
import logging
import psycopg2
import soundfile as sf
import speech_recognition as sr

from os import getenv
from typing import Any, Awaitable, Callable, Dict
from aiogram.utils.chat_action import ChatActionSender
from psycopg2.extras import RealDictCursor

from pydub import AudioSegment

from aiogram.types import ( 
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton)

from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    Voice,
)

logger = logging.getLogger(__name__)

ADMINS = os.getenv("ADMINS")

async def save_voice_as_wav(bot: Bot, voice: Voice) -> str:
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
              voice_path = await save_voice_as_wav(bot, message.voice)
              transcribed_voice_text = await audio_to_text(voice_path)
              logger.debug(f'Transcribed voice message: {transcribed_voice_text}')
              return transcribed_voice_text
     except:
     	  await message.reply(text="Извините, не удалось распознать сообщение\n"
                                 "Попробуйте устранить акустические или артикуляторные помехи")

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

def get_all_users(table_name='session_store', count=False):
    conn = connect_to_db()
    cursor = conn.cursor()

    admins = [int(admin_id) for admin_id in ADMINS.split(',')]
    cursor.execute("SELECT full_name, user_id, created_at, phone_number, selected_address, selected_guests, "
                          "selected_age, check_in_date, check_out_date FROM session_store" 
                          "WHERE user_id NOT IN %s", (tuple(admins),)) ##WHERE user_id NOT IN %s", (tuple(admins),)
    all_users_data = cursor.fetchall()

    if count:
        return len(all_users_data)
    else:
        return all_users_data

def admin_keyboard(user_telegram_id: int):
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

def get_images_from_directory(directory_path):
    images = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.jpeg')):
            images.append(os.path.join(directory_path, filename))
    return images