import os
import re
import sys
import asyncio
import logging
import requests

from os import getenv
from typing import Any, Awaitable, Callable, Dict, List
from aiogram import types, F, Router, Bot, flags, Dispatcher
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.methods.send_contact import SendContact
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import (
    CallbackQuery,
    Message,
    FSInputFile,
    User,
    Update
)
from aiogram_dialog import (
    Dialog, 
    DialogManager, 
    setup_dialogs, 
    StartMode, 
    Window, 
    DialogProtocol, 
    ShowMode, 
    Data
)
from aiogram_dialog.widgets.text import Format, Const, List
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Checkbox, Button, Url, Back, Row, Cancel, Start, Next, Back
)
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from aiogram.fsm.storage.memory import MemoryStorage
storage = MemoryStorage()

from collections import defaultdict

from modules.chain_definition import (
     conversational_rag_chain_for_metadata_search, 
     memory)
     #conversational_rag_chain_for_description_search)

from filters.filters import KeywordFilter, TrueFilter, HasPhoneNumberFilter
from utils.utils import get_images_from_directory, connect_to_db, get_all_users

# Ids and mini-functions for dialog-aiogram framework
from context_vault.context_vault import (
     BOT_REPLIES, 
     ADDRESS_CHOICES, 
     GUEST_CHOICES, 
     AGE_CHOICES)

logger = logging.getLogger(__name__)
trigger_router = Router()

EXTEND_BTN_ID = "extend"
EXTEND_CATALOG_ID = "extended_catalog"

ADDRESS_1_ID = "address_1"
ADDRESS_2_ID = "address_2"
ADDRESS_3_ID = "address_3"
ADDRESS_4_ID = "address_4"

ONE_GUEST_ID = "one"
TWO_GUEST_ID = "two"
THREE_GUEST_ID = "three"
MORE_GUEST_ID = "more_than_3"

old_GUEST_ID = "old"
adult_GUEST_ID = "adult"
young_GUEST_ID = "young"
little_GUEST_ID = "little"

ADMINS = os.getenv("ADMINS")

class Form(StatesGroup):
    START = State()
    address = State()
    guests = State()
    age = State()
    check_in_date = State()
    check_out_date = State()
    query = State()

class DialogFaq(StatesGroup):
    START = State()
    address = State()
    describe = State()

class Booking(StatesGroup):
    START = State()

async def mode_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
     if dialog_manager.find(EXTEND_BTN_ID).is_checked():
          return {
             "extended_str": "включен",
             "extended": True,
         }
     elif dialog_manager.find(EXTEND_BTN_ID).is_checked() == False:
         return {
             "extended_str": "отключен",
             "extended": False,
         }

async def address_getter(dialog_manager: DialogManager, **kwargs) -> dict: 
    user_id = dialog_manager.event.from_user.id

    address_ids = [ADDRESS_1_ID, ADDRESS_2_ID, ADDRESS_3_ID, ADDRESS_4_ID]
    selected_address = None
    for checkbox_id in address_ids:
        if dialog_manager.find(checkbox_id).is_checked():
            if selected_address is None:
                selected_address = ADDRESS_CHOICES[checkbox_id]
            else:
                selected_address.append(ADDRESS_CHOICES[checkbox_id])
    address_dict = {"address": selected_address}
    address_value = f"{selected_address['address']}"

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE session_store SET selected_address = %s WHERE user_id = %s", (address_value, user_id))
    conn.commit()
    return address_dict

async def guests_getter(dialog_manager: DialogManager, **kwargs) -> dict: 
    user_id = dialog_manager.event.from_user.id

    guest_ids = [ONE_GUEST_ID, TWO_GUEST_ID, THREE_GUEST_ID, MORE_GUEST_ID]
    selected_guests = None
    for checkbox_id in guest_ids:
        if dialog_manager.find(checkbox_id).is_checked():
            if selected_guests is None:
                 selected_guests = GUEST_CHOICES[checkbox_id]
            else:
                 selected_guests.append(GUEST_CHOICES[checkbox_id])
    guests_dict = {"guests": selected_guests}
    guests_value = f"{selected_guests['guests']}"

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE session_store SET selected_guests = %s WHERE user_id = %s", (guests_value, user_id))
    conn.commit()
    return guests_dict

async def age_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    user_id = dialog_manager.event.from_user.id

    age_ids = [old_GUEST_ID, adult_GUEST_ID, young_GUEST_ID, little_GUEST_ID]
    selected_ages = None

    for checkbox_id in age_ids:
        if dialog_manager.find(checkbox_id).is_checked():
            if selected_ages is None:
                selected_ages = AGE_CHOICES[checkbox_id]
            else:
                selected_ages.append(AGE_CHOICES[checkbox_id])
    ages_dict = {"ages": selected_ages}
    ages_value = f"{selected_ages['ages']}"

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE session_store SET selected_age = %s WHERE user_id = %s", (ages_value, user_id))
    conn.commit()
    return ages_dict

async def check_in_on_input(message: Message, 
                            dialog: DialogProtocol, 
                            dialog_manager: DialogManager):
    dialog_manager.dialog_data["check_in_date"] = message.text
    
    user_answer = message.text
    user_id = dialog_manager.event.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE session_store SET check_in_date = %s WHERE user_id = %s", (user_answer, user_id))
    conn.commit()
    await dialog_manager.next() 

async def check_out_on_input(message: Message, 
                             dialog: DialogProtocol, 
                             dialog_manager: DialogManager):
    dialog_manager.dialog_data["check_out_date"] = message.text
    
    user_answer = message.text
    user_id = dialog_manager.event.from_user.id
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE session_store SET check_out_date = %s WHERE user_id = %s", (user_answer, user_id))
    conn.commit()
    await dialog_manager.next() 

async def close_subdialog(callback: CallbackQuery, button: Button,
                          dialog_manager: DialogManager):
    await dialog_manager.done(result={'address': selected_address, 
                                      'guests': selected_guests, 
                                      'age': selected_age})

async def selected_button_clicked(callback: CallbackQuery, 
                                  button: Button, 
                                  dialog_manager: DialogManager):
    await dialog_manager.next()

async def address_button_clicked(CallbackQuery, 
                                 button: Button, 
                                 dialog_manager: DialogManager):
    dialog_manager.dialog_data["address"] = await address_getter(dialog_manager)
    address = await address_getter(dialog_manager)
    if address["address"] is not None:
         await dialog_manager.next()
    else:
         pass

async def guests_button_clicked(callback: CallbackQuery, 
                                button: Button, 
                                dialog_manager: DialogManager):
    dialog_manager.dialog_data["guests"] = await guests_getter(dialog_manager)
    guests = await guests_getter(dialog_manager)
    address = await address_getter(dialog_manager)

    if guests["guests"] == "более трех человек":
         await callback.message.answer(f"Квартира по адресу {address['address']} не может вместить"
                                       " более трех человек, поскольку в ней нет достаточного" 
                                       " количества спальных мест.")
         await callback.message.answer(BOT_REPLIES['additional-message'])
         await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
    elif guests["guests"] is None:
         pass
    else:
         await dialog_manager.next()

async def age_button_clicked(callback: CallbackQuery, 
                             button: Button, 
                             dialog_manager: DialogManager):
    dialog_manager.dialog_data["age"] = await age_getter(dialog_manager)
    age = await age_getter(dialog_manager)
    address = await address_getter(dialog_manager)

    if age["ages"] == "до 21":
         await callback.message.answer(f"Прошу прощения, мы можем заключить договор только"
                                        " с гостями, которым <b>исполнился 21 год</b>")
         await callback.message.answer(f"Всего доброго, ждем вас в сопровождении взрослых "
                                        "на {address['address']}!")
         await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
    elif age["ages"] is None:
         pass
    else:
         await dialog_manager.next()

async def price_get_data(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
             "address": dialog_manager.dialog_data,
             "guests": dialog_manager.dialog_data,
             "age": dialog_manager.dialog_data,
             "check_in_date": dialog_manager.dialog_data,
             "check_out_date": dialog_manager.dialog_data
    }

async def check_apology(bot_response):
    apology_pattern = r"(извините|к сожалению|не могу|прошу прощения|приношу извинения|нет)"
    if re.search(apology_pattern, bot_response, re.IGNORECASE):
        return True
    else:
        return False

async def main_process_result(start_data: Data, result: Any, dialog_manager: DialogManager):
    logger.debug(f'Data: {result}')

async def price_search_handler(callback: CallbackQuery, 
                               button: Button, 
                               dialog_manager: DialogManager):
    chat_id = dialog_manager.event.from_user
    #user_id = dialog_manager.event.from_user.id
    #conn = connect_to_db()
    #cursor = conn.cursor()
    #cursor.execute("SELECT session_id FROM session_store WHERE user_id = %s", (user_id,))
    #data_extracted = cursor.fetchone()
    #session_id = data_extracted["session_id"]

    address = await address_getter(dialog_manager)
    guests = await guests_getter(dialog_manager)
    formatted_prompt = f"Насколько хорошо квартира по адресу {address['address']} подойдет"
                        " для {guests['guests']}? Укажи стоимость"
    #formatted_prompt = f"Квартира по адресу {address['address']} подойдет для {guests['guests']}?" 
    #" Укажи стоимость, но ни в коем случае НИКОГДА не говори для скольки человек указываешь стоимость."
    chat_history = "Меня заинтересовало"
    memory.clear()
    bot_response = conversational_rag_chain_for_metadata_search.invoke({"question": formatted_prompt, 
                                                                        "chat_history": chat_history}) 
    memory.clear()
    bot_answer = bot_response['answer']
    #bot_response = conversational_rag_chain_for_metadata_search.invoke({"input": formatted_prompt}, config={"configurable": {"session_id": session_id}})
    #bot_answer = bot_response['answer']
    await callback.message.answer(bot_answer)
    
    apology_detected = await check_apology(bot_answer)
    if apology_detected:
    #if guests['guests'] == 'троих человек':
        await callback.message.answer(BOT_REPLIES['exception-answer'])
        await callback.message.answer("Не стесняйтесь попросить найти <u>фотографии</u>, "
                                      "если еще не видели (только не забудьте указать точный адрес)")
        await callback.message.answer(BOT_REPLIES['admin-number-3'])
        await dialog_manager.start(Booking.START)
    else:
        await callback.message.answer("Не стесняйтесь попросить найти <u>фотографии</u>, если "
                                      "еще не видели (только не забудьте указать точный адрес)")
        await callback.message.answer(BOT_REPLIES['admin-number-2'])
        await dialog_manager.start(Booking.START)

    #    formatted_prompt = f"Какие есть варианты для {guests['guests']}? Какой адрес, стоимость и почему стоит выбрать эту квартиру"
    #    #bot_response_2 = formatted_prompt
    #    bot_response_2 = conversational_rag_chain_for_metadata_search.invoke({"input": formatted_prompt}, config={"configurable": {"session_id": session_id}})
    #    bot_answer_2 = bot_response_2['answer']
    #    await callback.message.answer(bot_answer_2)

form_dialog = Dialog(
    Window(
        Format(
            "Режим поиска предполагает, что вы еще не выбрали квартиру\n\n"
            "Сейчас режим поиска {extended_str}.\n"
        ),
        Const(
            "В этом случае рекомендуем обратиться в раздел "
            "каталога, нажмите на меню около поля ввода ⬇️",
            when="extended",
        ),
        Row(
            Checkbox(
                checked_text=Const("☑️ Режим поиска"),
                unchecked_text=Const(" Режим поиска"),
                id=EXTEND_BTN_ID,
            ),
            Button(Const("Квартира выбрана"), id="address", on_click=selected_button_clicked),
        ),
        MessageInput(Cancel()),
        state=Form.START,
        getter=mode_getter,
    ),
    Window(
        Const("Отлично, тогда уточните"),
        Checkbox(
            checked_text=Const(BOT_REPLIES['address-1-with-tooltip']),
            unchecked_text=Const(BOT_REPLIES['address-1']),
            id=ADDRESS_1_ID,
            ),
        Checkbox(
            checked_text=Const(BOT_REPLIES['address-2-with-tooltip']),
            unchecked_text=Const(BOT_REPLIES['address-2']),
            id=ADDRESS_2_ID,
            ),
        Checkbox(
            checked_text=Const(BOT_REPLIES['address-3-with-tooltip']),
            unchecked_text=Const(BOT_REPLIES['address-3']),
            id=ADDRESS_3_ID,
            ),
        Checkbox(
            checked_text=Const(BOT_REPLIES['address-4-with-tooltip']),
            unchecked_text=Const(BOT_REPLIES['address-4']),
            id=ADDRESS_4_ID,
            ),
        Row(
            Back(text=Const("Назад")),
            Button(text=Const("Далее"), id="guests", on_click=address_button_clicked)),
        state=Form.address,
        getter=address_getter,
    ),
    Window(
        Const("Укажите общее количество гостей, пожалуйста"),
        Checkbox(
            checked_text=Const("☑️ Один"),
            unchecked_text=Const("Один"),
            id=ONE_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ Двое"),
            unchecked_text=Const("Двое"),
            id=TWO_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ Трое"),
            unchecked_text=Const("Трое"),
            id=THREE_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ Больше"),
            unchecked_text=Const("Больше"),
            id=MORE_GUEST_ID,
            ),
        Row(
            Back(text=Const("Назад")),
            Button(text=Const("Сохранить"), id="age", on_click=guests_button_clicked)),
        state=Form.guests,
        getter=guests_getter,
    ),
    Window(
        Const("Укажите возраст того, с кем будем заключать договор"),
        Checkbox(
            checked_text=Const("☑️ Менее 21"),
            unchecked_text=Const("Менее 21"),
            id=little_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ 21-30"),
            unchecked_text=Const("21-30"),
            id=young_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ 30-40"),
            unchecked_text=Const("30-40"),
            id=adult_GUEST_ID,
            ),
        Checkbox(
            checked_text=Const("☑️ Более 40"),
            unchecked_text=Const("Более 40"),
            id=old_GUEST_ID,
            ),
        Row(
            Back(text=Const("Назад")),
            Button(text=Const("Сохранить"), id="query", on_click=age_button_clicked)),
        state=Form.age,
        getter=age_getter,
    ),
    Window(
        Const("Поняла, когда вы планируете заселиться в квартиру? "
              "Пожалуйста, напишите в ответ дату заезда"
              "в формате ДД.ММ. и время прибытия в формате ЧЧ:ММ\n\n"
              "Пожалуйста, ничего лишнего! 🤫\n"
              "Например, 19 октября в 12:00"),
        MessageInput(check_in_on_input),
        state=Form.check_in_date,
        preview_add_transitions=[Next()],
    ),
    Window(
        Const("Отличный день!\nИ последняя просьба: напишите дату "
              "заезда аналогично в формате ДД.ММ. "
              "и время прибытия ЧЧ:ММ\n\nСнова прошу предоставить "
              "только необходимые сведения!\n"
              "Например, 20 октября в 18:00"),
        MessageInput(check_out_on_input),
        state=Form.check_out_date,
        preview_add_transitions=[Next()],
    ),
    Window(
        Format("Мы почти у цели!\nДополнительно проверим наличие " 
               "по адресу {dialog_data[address][address]}... ⬇️"),
        Button(text=Const("Узнать стоимость"), 
               id="process_query_id", 
               on_click=price_search_handler),
        MessageInput(Cancel()),
        state=Form.query
    ),
    getter=price_get_data,
    on_process_result=main_process_result
)

booking = Dialog(
    Window(
        Format("Если хотите, можете забронировать ⬇️"),
        Url(
            Const("Забронировать"),
            Const(BOT_REPLIES["booking-link"]),
        ),
        MessageInput(Cancel()),
        state=Booking.START,
    ),
)

######################################################### CATALOG ####################################################################

async def catalog_next_button_clicked(callback: CallbackQuery, 
                                      button: Button, 
                                      dialog_manager: DialogManager):
    dialog_manager.dialog_data["address"] = await address_getter(dialog_manager)
    await dialog_manager.next()

async def catalog_search_button_handler(callback: CallbackQuery, 
                                        button: Button, 
                                        dialog_manager: DialogManager):
    user_name = callback.from_user.username
    address = await address_getter(dialog_manager)

    address_value = address['address']
    number_value = BOT_REPLIES['number_value']
    if address_value == BOT_REPLIES['addres-value-1']:
        await callback.message.answer(text=BOT_REPLIES['description-address-1'])
        await callback.message.answer(text=BOT_REPLIES['guide-to-send-photos'])
        await callback.message.answer(text=BOT_REPLIES['price'])
        await callback.message.answer(f"{user_name}, наш телефон для связи: {number_value}")
    elif address_value == BOT_REPLIES['addres-value-2']:
        await callback.message.answer(text=BOT_REPLIES['description-address-2'])
        await callback.message.answer(text=BOT_REPLIES['guide-to-send-photos'])
        await callback.message.answer(text=BOT_REPLIES['price'])
        await callback.message.answer(f"{user_name}, наш телефон для связи: {number_value}")
    elif address_value == BOT_REPLIES['addres-value-3']:
        await callback.message.answer(text=BOT_REPLIES['description-address-3'])
        await callback.message.answer(text=BOT_REPLIES['guide-to-send-photos'])
        await callback.message.answer(text=BOT_REPLIES['price'])
        await callback.message.answer(f"{user_name}, наш телефон для связи: {number_value}")
    elif address_value == BOT_REPLIES['addres-value-4']:
        await callback.message.answer(text=BOT_REPLIES['description-address-4'])
        await callback.message.answer(text=BOT_REPLIES['guide-to-send-photos'])
        await callback.message.answer(text=BOT_REPLIES['price'])
        await callback.message.answer(f"{user_name}, наш телефон для связи: {number_value}")
'''
async def catalog_search_button_handler(callback: CallbackQuery, button: Button, dialog_manager: DialogManager): # session_id: str = None
    chat_id = dialog_manager.event.from_user
    user_id = dialog_manager.event.from_user.id
    user_name = callback.from_user.username
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM session_store WHERE user_id = %s", (user_id,))
    data_extracted = cursor.fetchone()
    session_id = data_extracted["session_id"]

    address = await address_getter(dialog_manager)

    formatted_prompt = f"Расскажи о квартире по адресу {address['address']}! Почему стоит выбрать эту кватиру для посуточной аренды?"
    #bot_response = formatted_prompt
    bot_response = conversational_rag_chain_for_description_search.invoke({"input": formatted_prompt}, config={"configurable": {"session_id": session_id}})
    bot_answer = bot_response['answer']
    await callback.message.answer(text=bot_answer)
    await callback.message.answer("Если еще не видели, как выглядит квартира, не стесняйтесь попросить показать <u>фотографии</u> (только не забудьте указать точный адрес)")
    await callback.message.answer(f"Для того, чтобы узнать стоимость, рекомендуем обратиться в раздел стоимости, нажмите на меню возле поля ввода ⬇️")
    await callback.message.answer(f"{user_name}, наш телефон для связи: +7(913)-029-0023 ✨")

    await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
    await dialog_manager.start(Booking.START)
'''
async def catalog_getter(dialog_manager: DialogManager, **kwargs) -> Dict[str, Any]:
    if dialog_manager.find(EXTEND_CATALOG_ID).is_checked():
        return {
            "extended_catalog_str": "включен",
            "extended_catalog": True,
        }
    elif dialog_manager.find(EXTEND_CATALOG_ID).is_checked() == False:
        return {
            "extended_catalog_str": "отключен",
            "extended_catalog": False,
        }

faq_dialog = Dialog(
     Window(
          Const("Уже выбрали или желаете узнать о квартире подробнее?"),
          Const(
            "В этом случае рекомендуем обратиться в раздел стоимости, нажмите на меню возле поля ввода ⬇️",
            when="extended_catalog",
          ),
          Row(
               Checkbox(
                  checked_text=Const("☑️ Квартира выбрана"),
                  unchecked_text=Const("Квартира выбрана"),
                  id=EXTEND_CATALOG_ID,
               ),
               Button(Const("Узнать подробнее"), id="describe", on_click=catalog_next_button_clicked)
          ),
          MessageInput(Cancel()),
          state=DialogFaq.START,
          getter=catalog_getter,
     ),
     Window(
         Const("Благодарю за интерес! О какой квартире вы бы хотели узнать подробнее?"),
         Checkbox(
             checked_text=Const(BOT_REPLIES['address-1-with-tooltip']),
             unchecked_text=Const(BOT_REPLIES['address-1']),
             id=ADDRESS_1_ID,
             ),
         Checkbox(
             checked_text=Const(BOT_REPLIES['address-2-with-tooltip']),
             unchecked_text=Const(BOT_REPLIES['address-2']),
             id=ADDRESS_2_ID,
             ),
         Checkbox(
             checked_text=Const(BOT_REPLIES['address-3-with-tooltip']),
             unchecked_text=Const(BOT_REPLIES['address-3']),
             id=ADDRESS_3_ID,
             ),
         Checkbox(
             checked_text=Const(BOT_REPLIES['address-4-with-tooltip']),
             unchecked_text=Const(BOT_REPLIES['address-4']),
             id=ADDRESS_4_ID,
             ),
         Row(
             Back(text=Const("Назад")),
             Button(text=Const("Далее"), id="guests", on_click=catalog_next_button_clicked)),
         state=DialogFaq.address,
         getter=address_getter,
    ),
    Window(
        Format("Нажмите на кнопку, чтобы запустить поиск информации о {dialog_data[address][address]}"),
        Button(text=Const("Поиск"), 
               id="catalog_process_query_id", 
               on_click=catalog_search_button_handler),
        MessageInput(Cancel()),
        state=DialogFaq.describe,
    ),
    getter=price_get_data,
    on_process_result=main_process_result
)

trigger_router.include_router(form_dialog)
trigger_router.include_router(faq_dialog)
trigger_router.include_router(booking)
setup_dialogs(trigger_router)

@trigger_router.message(CommandStart(), TrueFilter())
async def process_start_command(message: Message):
     await message.answer(f'{message.from_user.full_name}, на связи! 🫡') 
     await message.answer(text=BOT_REPLIES['/start'])

@trigger_router.message(F.text == "/price")
async def price(message: Message, dialog_manager: DialogManager):
     await dialog_manager.start(Form.START, mode=StartMode.RESET_STACK)

@trigger_router.message(F.text == "/faq")
async def faq(message: Message, dialog_manager: DialogManager):
     await message.answer(text=BOT_REPLIES['/faq'])
     await dialog_manager.start(DialogFaq.START, mode=StartMode.RESET_STACK)

@trigger_router.message(F.text == "/help")
async def help(message: Message):
    await message.answer(BOT_REPLIES['/help-1'])
    await message.answer(BOT_REPLIES['/help-2'])
    await message.answer(BOT_REPLIES['/help-3'])
    await message.answer(BOT_REPLIES['/help-4'])
    await message.answer(BOT_REPLIES['/help-5'])
    await message.answer(BOT_REPLIES['/help-6'])

@trigger_router.message(F.text == "/call")
async def operator(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        admins = [int(admin_id) for admin_id in ADMINS.split(',')]
        full_name = message.from_user.full_name
        user_id = message.from_user.id
        text = f'Пользователь по имени {full_name} желает связаться!\nВот, что удалось узнать про него:\n'

        all_users_data = get_all_users()

        for user in all_users_data:
            if user.get("user_id") == user_id:
                text += (
                    f'\nТелеграм ID: {user_id}\n'
                )
                if user.get("user_id") in admins:
                    text += f"\n{full_name} — один из администраторов! Чтобы посмотреть содержимое базы данных пользователей, напишите команду 'Панель' с большой буквы в ос>
                    text += (f'〰〰〰〰〰〰〰〰〰\n\n')
                    continue

                if user.get("phone_number") is not None:
                    text += f'😱 Номер: +{user.get("phone_number")} 😱\n'

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

        for chat_id in admins:
            bot_key = os.getenv("NOTIFICATION_BOT_TOKEN")
            send_message_url = f'https://api.telegram.org/bot{bot_key}/sendMessage?chat_id={chat_id}&text={text}'
            requests.post(send_message_url)
        await message.answer("Отправила уведомление! Если хотите получить обратную связь быстрее, ниже представлен номер")
        await bot.send_contact(chat_id=message.chat.id, phone_number=BOT_REPLIES['number_value'], first_name="Елена")
        await message.answer(BOT_REPLIES['/operator-1'])
        await message.answer(BOT_REPLIES['/operator-2'])
        await message.answer("🌿 Можете также оставить свой номер телефона, если хотите (формат: +79810002222)")

# Process any text if a filter return true
@trigger_router.message(F.text, KeywordFilter(BOT_REPLIES['address-keywords-1']))
async def message_with_city_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing text with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['search-1'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(5)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/city/"
        album_builder = MediaGroupBuilder(caption="Вот, что у меня нашлось по этом поводу!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@trigger_router.message(F.text, KeywordFilter(BOT_REPLIES['address-keywords-2']))
async def message_with_address_4_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing text with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['search-2'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-4/"
        album_builder = MediaGroupBuilder(caption="Собрала для вас несколько подходящих фотографий!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@trigger_router.message(F.text, KeywordFilter(BOT_REPLIES['address-keywords-3']))
async def message_with_address_2_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing text with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['search-3'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-2/"
        album_builder = MediaGroupBuilder(caption="Может подойти!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@trigger_router.message(F.text, KeywordFilter(BOT_REPLIES['address-keywords-4']))
async def message_with_address_1_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(3)
        logger.debug('Entered handler processing text with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['search-4'])
    await asyncio.sleep(3)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-1/"
        album_builder = MediaGroupBuilder(caption="Готово!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@trigger_router.message(F.text, KeywordFilter(BOT_REPLIES['address-keywords-5']))
async def message_with_address_3_photo_request(message: Message, bot: Bot):
    async with ChatActionSender.typing(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(2)
        logger.debug('Entered handler processing text with keywords: guess about request to send photos')
        await message.reply(BOT_REPLIES['search-5'])
    await asyncio.sleep(2)

    async with ChatActionSender.upload_photo(bot=bot, chat_id=message.from_user.id):
        await asyncio.sleep(4)
        chat_id = message.from_user.id
        directory_path = "/home/pino/perseus_chat/var/data/media/address-3/"
        album_builder = MediaGroupBuilder(caption="Вот несколько снимков, "
            "которые, на мой взгляд, подойдут!")
        images = get_images_from_directory(directory_path)
        for image_path in images:
            album_builder.add(type="photo", media=FSInputFile(image_path))
        media = album_builder.build()
        await bot.send_media_group(chat_id, media)

@trigger_router.message(F.text, HasPhoneNumberFilter())
async def message_with_phone_numbers(message: Message, phone_numbers: str):
    admins = [int(admin_id) for admin_id in ADMINS.split(',')]
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    conn = connect_to_db()
    cursor = conn.cursor()
    
    phone_str = f'{", ".join(phone_numbers)}' 

    cursor.execute(
        "UPDATE session_store SET phone_number = %s WHERE user_id = %s", (phone_str, user_id)
    )
    conn.commit()
    for chat_id in admins:
        text = f'Пользователь по имени 🔫 {full_name}🔫  оставил номер '
                '{", ".join(phone_numbers)}!\n\nТелеграм ID: {user_id}'
        bot_key = os.getenv("NOTIFICATION_BOT_TOKEN")
        send_message_url = f'https://api.telegram.org/bot{bot_key}/sendMessage?chat_id={chat_id}&text={text}'
        requests.post(send_message_url)

    await message.reply(
        f'Благодарю! Передам номер '
        f'{", ".join(phone_numbers)} администратору'
        )

@trigger_router.message(F.text.contains('🔙 Назад'))
async def back_button(message: Message, bot: Bot):
    pass 