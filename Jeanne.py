#       900865796 моя
# создать pip freeze > requirements.txt
# установить pip install -r requirements.txt




import sqlite3
import os
import asyncio
import random
import time
import requests

#import update

#from bs4 import BeautifulSoup

from array import *

from datetime import datetime, timedelta

import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatMember
from aiogram.filters import Command
from aiogram.types import Message


from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData


from aiogram.types.input_file import FSInputFile

from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar

from config import *




bot = Bot(token=TOKEN)
dp = Dispatcher()



HISTORY_DIR = "data/history"
logging.basicConfig(level=logging.INFO)

logging.basicConfig(level=logging.INFO, filename='data/variables/log.txt', format='%(asctime)s - %(message)s')

class ADMINS(StatesGroup):
    idtg = State()
    role = State()
    delete = State()
    help = State()
    text = State()
    link = State()
    desc = State()
    minus = State()
    generate = State()

class CHAN(StatesGroup):
    name_chan = State()
    id_chan = State()
    link_chan = State()

class GIVEAWAY(StatesGroup):
    chan_id = State()
    name = State()
    post = State()
    link = State()
    giveaway_end = State()
    date_end = State()
    stop_reason = State()
    name_file = State()
    much_win = State()
    win_numbers = State() 

class manual_send(StatesGroup):
    idtg = State()
    name = State()
    password = State()



# Создаем БД админов
con = sqlite3.connect('data/db/role/admin.db')
cur = con.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            idtg VARCHAR (20), 
            name VARCHAR (40), 
            nick VARCHAR (40),
            role VARCHAR (20)
            )''')
cur.execute('''
    CREATE TABLE IF NOT EXISTS login(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            login_app VARCHAR (200), 
            password_app VARCHAR (200),
            time_app  VARCHAR (200)
            )''')

con.commit()
cur.close()
con.close()

# Создаем БД записок
con = sqlite3.connect('data/db/notepad/notepad.db')
cur = con.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS note(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            admin_nick VARCHAR (20), 
            link VARCHAR (800), 
            desc VARCHAR (400),
            text VARCHAR (20)
            )''')
con.commit()
cur.close()
con.close()

# Создаем БД каналов
con = sqlite3.connect('data/db/giveaway/chan_data.db')
cur = con.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS channals(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_chan VARCHAR (20), 
            name VARCHAR (40), 
            link VARCHAR (40)
            )''')
con.commit()
cur.close()
con.close()

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    try:
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            tributes = (cur.execute('SELECT COUNT (*) from tributes').fetchone())[0]

    except:
        pass
    await state.clear()
    user_id = message.from_user.id
    name = message.chat.first_name
    nick = message.from_user.username

    items = get_sorted_items(HISTORY_DIR)
    files = items
    
    MAX_FILES = 12
    if len(files) > MAX_FILES:
        # Получаем список файлов для удаления (самые старые)
        files_to_delete = files[MAX_FILES:]
        for file in files_to_delete:
            try:
                os.remove(file['path'])
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
    
    if is_user_admin(user_id):
        role = role_in_db(user_id)
        board = InlineKeyboardBuilder()
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        # Обновляем имя и ник админа
        cur.execute(f'UPDATE admins SET name = ? wHERE idtg = {user_id} ', [name])
        cur.execute(f'UPDATE admins SET nick = ? wHERE idtg = {user_id}', [nick])
        con.commit()
        con.close()

        if role == 'master':
            board.add(types.InlineKeyboardButton(text="🛠Продлить WebApp🛠", callback_data="selenium_update"))
            board.row(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.row(types.InlineKeyboardButton(text="🎁Управление розыгрышем🎁", callback_data="giveaway"))
        board.row(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.row(types.InlineKeyboardButton(text="Инструменты", callback_data="start_notepad"))
        board.row(types.InlineKeyboardButton(text="Проверить WebApp", web_app=WebAppInfo(url='https://firestormwebapp.pythonanywhere.com/start')))
        board.row(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        board.adjust(1)
        try:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                number = int((cur.execute('SELECT COUNT (*) from giveaways_data').fetchone())[0])
                giveaway_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_msg = (cur.execute('SELECT msg_id FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            link = (f'{giveaway_link}' + '/' + f'{giveaway_msg}')
            current_date = datetime.today()
            date_obj = datetime.strptime(giveaway_end, "%d_%m_%Y")
            delta = (date_obj - current_date).days
            with sqlite3.connect('data/db/role/admin.db') as con:
                cur = con.cursor()
                time_app = (cur.execute('SELECT time_app FROM login').fetchone())[0]
            date_obj = datetime.strptime(time_app, "%Y-%m-%d")
            delta_app = (date_obj - current_date).days
            sent_message = await message.answer (f'👋🏻 <i>Привет, {name}!!! 👋🏻\nРозыгрыш №{number} <b><u>активен</u></b>\nПроводиться в канале <a href="{giveaway_link}">{giveaway_name}</a> \nПосмотреть пост можно тут 👉🏻<a href="{link}">ЖМЯК</a>\nДо конца розыгрыша осталось <b><u>{delta}</u></b> дней\n<b>WebApp будет активно еще <u>{delta_app}</u> дней</b>\nВыбирай нужный пункт</i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            with sqlite3.connect('data/db/role/admin.db') as con:
                cur = con.cursor()
                time_app = (cur.execute('SELECT time_app FROM login').fetchone())[0]
            current_date = datetime.today()
            date_obj = datetime.strptime(time_app, "%Y-%m-%d")
            delta_app = (date_obj - current_date).days
            sent_message = await message.answer (f"👋🏻 <i>Привет, {name}!!! 👋🏻\n<b>WebApp будет активно еще <u>{delta_app}</u> дней</b>\nВыбирай нужный пункт</i>", parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    
    else:
        # Если не админ, проверяем наличие реги
        idtg = message.from_user.id
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            exist = cur.execute('SELECT 1 FROM tributes WHERE id_tg = ?', [idtg]).fetchone()
        
        # Если пользователь зарегистрирован, то проверяем розыгрыш на активность
        if exist:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                act = 'active'
                cur = con.cursor()
                giveaway_act = cur.execute('SELECT 1 FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone()
        
            # Если розыгрыш завершен, проверяем на выигрыш
            if not giveaway_act:
                try:
                    with sqlite3.connect('data/db/giveaway/winners.db') as con:
                        cur = con.cursor()
                        name = (cur.execute('SELECT us_name FROM winners WHERE id_tg = ?', [idtg]).fetchone())[0]
                        password = (cur.execute('SELECT password FROM winners WHERE id_tg = ?', [idtg]).fetchone())[0]
                        board = InlineKeyboardBuilder()
                        board.add(types.InlineKeyboardButton(text="Посмотреть итог розыгрыша", web_app=WebAppInfo(url='https://firestormwebapp.pythonanywhere.com/start')))
                        try:
                            await message.answer (f'<i> Приветствую, {name}!!! 👋🏻\nВы победили в розыгрыше от <b><a href="https://firestorm-servers.com/ru">Firestorm</a></b> 🥳\nПароль для получение выигрыша\n👉🏻 {password} 👈🏻\nСообщите его в личные сообщения дискорд <u>Aorid</u> либо <u>Retmex</u> и получите свой приз 🏆 !</i>', disable_web_page_preview=True, parse_mode="HTML", reply_markup=board.as_markup())
                        except Exception as e:
                            print(f"Не удалось выслать пароль победителю, ошибка: {e}")
                except:
                    board = InlineKeyboardBuilder()
                    board.add(types.InlineKeyboardButton(text="Итог розыгрыша", web_app=WebAppInfo(url='https://firestormwebapp.pythonanywhere.com/start')))
                    await message.answer (f'<i>👋🏻 Приветствую, {name}! 👋🏻\nРозыгрыш завершен ✅\nРегистрация недоступна ❌\nРезультат проведенного розыгрыша можно посмотреть, нажав на кнопку ниже</i> 👇', parse_mode="HTML", reply_markup=board.as_markup())

            # Если розыгрыш НЕ завершен, но пользователь зареган
            else:
                with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                    cur = con.cursor()
                    giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                current_date = datetime.today()
                date_obj = datetime.strptime(giveaway_end, "%d_%m_%Y")
                delta = (date_obj - current_date).days
                try:
                    await message.answer (f'<i> Приветствую, {name}! 👋🏻\nВы уже зарегистрированы 😉\nДо конца розыгрыша осталось {delta} дней</i> 🗓️ ', parse_mode="HTML")
                except Exception as e:
                    print(f"розыгрыш НЕ завершен, но пользователь зареган: {e}")

        # Если реги нет 
        else:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                act = 'active'
                cur = con.cursor()
                giveaway_act = cur.execute('SELECT 1 FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone()
                giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
            current_date = datetime.today()
            date_obj = datetime.strptime(giveaway_end, "%d_%m_%Y")
            delta = (date_obj - current_date).days
            if not nick:
                nick = "MINUS"
            else:
                nick = "@" + nick
            
            # Если розыгрыш не активен
            if not giveaway_act:
                try:
                    board = InlineKeyboardBuilder()
                    board.add(types.InlineKeyboardButton(text="Итог розыгрыша", web_app=WebAppInfo(url='https://firestormwebapp.pythonanywhere.com/start')))
                    await message.answer (f'<i>👋🏻 Приветствую, {name}! 👋🏻\nРозыгрыш завершен ✅\nРегистрация недоступна ❌\nРезультат проведенного розыгрыша можно посмотреть, нажав на кнопку ниже</i> 👇', parse_mode="HTML", reply_markup=board.as_markup())
                except Exception as e:
                    print(f"Розыгрыш не активен, сообщение не отправилось: {e}")
            
            # Розыгрыш активен, регаем пользователя
            else:
                with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                    act = 'active'
                    cur = con.cursor()
                    chan_id = (cur.execute('SELECT chan_id FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
                try:
                    podpiska = await bot.get_chat_member(chat_id=chan_id, user_id=idtg)
                    podpiska = podpiska.status
                    if podpiska in ["member", "administrator", "creator"]:
                        #Пиздим аватар
                        user_id = message.from_user.id
                        user_info = await bot.get_user_profile_photos(user_id, limit=1)
                    # Проверяем, есть ли у пользователя аватар
                        if user_info.photos:
                       # Получаем file_id самого большого размера аватара
                            file_id = user_info.photos[0][-1].file_id
                           # Получаем информацию о файле
                            file_info = await bot.get_file(file_id)
                           # Скачиваем аватар
                            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                            response = requests.get(file_url)
                            # Сохраняем аватар в файл
                            with open(f"data/variables/scr/avatars/{idtg}.jpg", "wb") as avatar_file:
                                avatar_file.write(response.content)
                           # Функция для преобразования изображения в бинарный формат
                            with open(f"data/variables/scr/avatars/{idtg}.jpg", "rb") as file:
                                file.read()
                            # Преобразование изображения в бинарный формат
                            image_path = f'data/variables/scr/avatars/{idtg}.jpg'
                            ava = convert_image_to_binary(image_path)
                        else:
                            with open("data/variables/scr/no_ava.jpg", "rb") as file:
                                file.read()
                            image_path = 'data/variables/scr/no_ava.jpg'
                            ava = convert_image_to_binary(image_path)

                        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                            cur = con.cursor()
                            cur.execute('INSERT INTO tributes (id_tg, us_nick, us_name, podpis, us_ava) VALUES (?, ?, ?, ?, ?)', (idtg, nick, name, podpiska, ava))
                        try:
                            await message.answer (f'<i>👋🏻 Привет, {name}!!! 👋🏻\nРегистрация выполнена✅\nДо конца розыгрыша осталось {delta} дней 📆</i>', parse_mode="HTML")
#                            os.remove(f'data/variables/scr/avatars/{idtg}.jpg')
                        except Exception as e:
                            print(f"Регистрация выполнена\nДо конца розыгрыша осталось: {e}")
                        
                        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                            act = 'active'
                            cur = con.cursor()
                            chan_id = int((cur.execute('SELECT chan_id FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0])
                            msg_id = int((cur.execute('SELECT msg_id FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0])
                        board = InlineKeyboardBuilder()
                        board.add(types.InlineKeyboardButton(text=f"Регистрация ({tributes+1})", url='https://t.me/Firestorm_contest_bot'))
                        try:
                            await bot.edit_message_reply_markup(chat_id=chan_id, message_id=msg_id, reply_markup=board.as_markup())
                        except Exception as e:
                            print(f"Не удалось обновить клавиатуру после реги: {e}")

                    # Пользователь попытался зарегаться, но не подписан на канал
                    else:
                        try:
                            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                                act = 'active'
                                cur = con.cursor()
                                chan_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
                                chan_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
                            
                            await message.answer (f'<i> Приветствую, {name}! 👋🏻\nК сожалению, Вы не подписаны на канал <a href="{chan_link}"> {chan_name}</a>  😟</i>', parse_mode="HTML")
                        except Exception as e:
                            print(f"Вы не подписаны на канал 320: {e}")
                except Exception as e:
                    print (f"322 строка :{e}")
                    with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                        act = 'active'
                        cur = con.cursor()
                        chan_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
                        chan_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
                    try:
                        await message.answer (f'<i> Приветствую, {name}! 👋🏻\nК сожалению, Вы не подписаны на канал <a href="{chan_link}"> {chan_name}</a>  😟</i>', parse_mode="HTML")
                    except Exception as e:
                        print(f"Вы не подписаны на канал 326: {e}")


# Конвертация аватары в бинарный файл
def convert_image_to_binary(image_path):
    with open(image_path, 'rb') as file:
        return file.read()


@dp.callback_query(lambda c: c.data == "start_history")
async def process_browser(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await list_directory(callback_query.message, HISTORY_DIR)

# Обработчик удаление админа
@dp.callback_query(lambda c: c.data.startswith("adminminus_"))
async def adminminus(callback_query: types.CallbackQuery):
    await callback_query.answer()
    admin_id = callback_query.data.split("_", 1)[1]
    try:
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        cur.execute("DELETE FROM admins WHERE idtg = ?", (admin_id,))
        con.commit()
        con.close()
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        all = cur.execute("SELECT id FROM admins ORDER BY id DESC LIMIT 1")
        all = int((cur.fetchone())[0])
        board = InlineKeyboardBuilder()
        for i in range(1, all+1):
            try:
                nick = cur.execute(f'SELECT nick FROM admins WHERE id = ?', [i]).fetchone()
                idtg = cur.execute(f'SELECT idtg FROM admins WHERE id = ?', [i]).fetchone()
                nick = nick[0]
                idtg = idtg[0]
                board.add(types.InlineKeyboardButton(text=f"{nick}", callback_data=f"adminminus_{idtg}"))
            except:
                pass
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        await callback_query.message.edit_text("<i>Админ удален</i>", parse_mode="HTML", reply_markup=board.as_markup())
    except:
        board = InlineKeyboardBuilder()
        board.row(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Ошибка при удалении админа</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Обработчик чтения базы виннеров
@dp.callback_query(lambda c: c.data.startswith("log:"))
async def winners(callback_query: types.CallbackQuery):
    await callback_query.answer()
    file_path = callback_query.data.split(":", 1)[1]
    file_path = f"{HISTORY_DIR}" + "/log " + f"{file_path}"
    with open (file_path, 'r', encoding="utf-8") as file:
        winner_text = file.read()
    items = get_sorted_items(HISTORY_DIR)
    board = InlineKeyboardBuilder()
    files = items
    for file in files:
        button_text = (file['name']).split(" ", 1)[1]
        filename = button_text
        button_text = button_text.split(".", 1)[0]
        board.add(types.InlineKeyboardButton(text=button_text, callback_data=f"log:{filename}"))
    board.adjust(*[3] * len(files), 1)
    board.row(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    sent_message = await callback_query.message.edit_text(f"{winner_text}\n--------------------\n<i>Когда производился розыгрыш?\nВыбери дату окончания</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Обработчик чтения записной книжки
@dp.callback_query(lambda c: c.data.startswith("notepad_"))
async def notepad(callback_query: types.CallbackQuery):
    await callback_query.answer()
    i = callback_query.data.split("_", 1)[1]
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    nick = (cur.execute('SELECT admin_nick FROM note WHERE id = ?', [i]).fetchone())[0]
    link = (cur.execute('SELECT link FROM note WHERE id = ?', [i]).fetchone())[0]
    desc = (cur.execute('SELECT desc FROM note WHERE id = ?', [i]).fetchone())[0]
    text_base = (cur.execute('SELECT text FROM note WHERE id = ?', [i]).fetchone())[0]
    con.close()
    board = InlineKeyboardBuilder()
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    try:
        all = cur.execute("SELECT id FROM note ORDER BY id DESC LIMIT 1")
        all = int((cur.fetchone())[0])
        cur.execute("SELECT * FROM note")
        rows = cur.fetchall()
        for i in range (1, all+1):
            try:
                text = cur.execute("SELECT text FROM note WHERE id = ?", (i,)).fetchone()
                text = text[0]
                board.add(types.InlineKeyboardButton(text=f"{text}", callback_data=f"notepad_{i}"))
            except:
                pass
    except:
        pass
    con.close()
    board.add(types.InlineKeyboardButton(text="➕Добавить запись➕", callback_data="note_plus"))
    board.add(types.InlineKeyboardButton(text="➖Удалить запись➖", callback_data="note_minus"))
    board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
    board.adjust(*[1] * len(rows), 2, 1)
    sent_message = await callback_query.message.edit_text(f"<i>{text_base}\n{link}\n{desc}\n Добавил <b>@{nick}</b></i>", parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

@dp.callback_query(lambda c: c.data.startswith("chan_minus:"))
async def chan_minus (callback_query: types.CallbackQuery):
    await callback_query.answer()
    i = callback_query.data.split(":", 1)[1]
    con = sqlite3.connect('data/db/giveaway/chan_data.db')
    cur = con.cursor()
    cur.execute("DELETE FROM channals WHERE id = ?", (i,))    
    con.commit()
    con.close()
    con = sqlite3.connect('data/db/giveaway/chan_data.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM channals")
    rows = cur.fetchall()
    con.close()
    board = InlineKeyboardBuilder()
    try:
        for row in rows:
            board.add(types.InlineKeyboardButton(text=f"{row[2]}", callback_data=f"giveaway:{row[0]}"))
        board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
        board.add(types.InlineKeyboardButton(text="➖Удалить канал➖", callback_data="channal_minus"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(*[1] * len(rows), 2, 1)
        sent_message = await callback_query.message.edit_text(f"<i>Выбирай канал для запуска розыгрыша</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    except:
        board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text(f"<i>Все каналы удалены</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

# Старт розыгрыша (создание БД)
@dp.callback_query(lambda c: c.data.startswith("start_giveaway:"))
async def start_giveaway(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
        cur = con.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS giveaways_data(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    admin_start VARCHAR (20),
                    chan_name VARCHAR (30),
                    admin_end VARCHAR (20),
                    chan_id VARCHAR (20), 
                    chan_link VARCHAR (120),
                    msg_id VARCHAR (20),
                    giveaway_status VARCHAR (20),
                    giveaway_end VARCHAR (20),
                    giveaway_much_win VARCHAR (20)
                    )''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tributes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    id_tg VARCHAR (20),
                    us_nick VARCHAR (20),
                    us_name VARCHAR (20),
                    podpis VARCHAR (20),
                    us_ava BLOB
                    )''')   
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS loser(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    id_tg VARCHAR (20),
                    us_name VARCHAR (20),
                    reason VARCHAR (20)
                    )''') 
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS winners(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    id_tg VARCHAR (20),
                    us_nick VARCHAR (20),
                    us_name VARCHAR (20),
                    password VARCHAR (30),
                    us_ava BLOB
                    )''')
        
        con.commit()

    i = callback_query.data.split(":", 1)[1]
    con = sqlite3.connect('data/db/giveaway/chan_data.db')
    cur = con.cursor()
    text = (cur.execute("SELECT name FROM channals WHERE id_chan = ?", (i,)).fetchone())[0]
    link_chan = (cur.execute("SELECT link FROM channals WHERE id_chan = ?", (i,)).fetchone())[0]
    con.close()
    await state.set_state(GIVEAWAY.chan_id)
    await state.update_data(chan_id=i)
    await state.set_state(GIVEAWAY.link)
    await state.update_data(link=link_chan)
    await state.set_state(GIVEAWAY.name)
    await state.update_data(name=text)
    sent_message = await callback_query.message.edit_text(f'<i>Театр начинается с вешалки, а конкурс - с анонса\nТы решил запустить конкурс в канале <a href="{link_chan}">{text}</a>\nДля этого необходимо будет выбрать дату <b>окончания</b> розыгрыша, а затем мне нужен будет пост, которым ты запустишь конкурс\n\n<b>ВЫБИРАЙ ДАТУ</b></i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=await SimpleCalendar().start_calendar())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        giveaway_end = date.strftime("%d_%m_%Y")
        await state.set_state(GIVEAWAY.date_end)
        await state.update_data(date_end=giveaway_end)
        await state.set_state(GIVEAWAY.post)
        await callback_query.message.edit_text(f'<i>Фиксирую дату окончания: <u>{date.strftime("%d.%m.%Y")}</u>\nТеперь необходимо разобраться с постом.\n<b>Жду сейчас</b> от тебя фотографию с описанием <b><u>(одним постом, жду 10 минут)</u></b>\n</i>', parse_mode="HTML")



# Общий обработчик нажатий на кнопки
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    role = role_in_db(user_id)
    callback_data = callback_query.data
    name = callback_query.from_user.username
    nick = name
    logging.info(f"Юзер {nick} запрос: {callback_data}")
    data = callback_query.data
    await callback_query.answer()

    if data == "ok":
        await state.clear()
        name = callback_query.from_user.first_name
        items = get_sorted_items(HISTORY_DIR)
        files = items
        MAX_FILES = 12
        if len(files) > MAX_FILES:
            # Получаем список файлов для удаления (самые старые)
            files_to_delete = files[MAX_FILES:]
            for file in files_to_delete:
                try:
                    os.remove(file['path'])
                except Exception as e:
                    print(f"Ошибка при удалении: {e}")

        board = InlineKeyboardBuilder()
        if role  == 'master':
            board.add(types.InlineKeyboardButton(text="🛠Продлить WebApp🛠", callback_data="selenium_update"))
            board.add(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.add(types.InlineKeyboardButton(text="🎁Управление розыгрышем🎁", callback_data="giveaway"))
        board.add(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.add(types.InlineKeyboardButton(text="Инструменты", callback_data="start_notepad"))
        board.row(types.InlineKeyboardButton(text="Проверить WebApp", web_app=WebAppInfo(url='https://firestormwebapp.pythonanywhere.com/start')))
        board.add(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        board.adjust(1)
        try:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                number = int((cur.execute('SELECT COUNT (*) from giveaways_data').fetchone())[0])
                giveaway_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_msg = (cur.execute('SELECT msg_id FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
                giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            link = (f'{giveaway_link}' + '/' + f'{giveaway_msg}')
            current_date = datetime.today()
            date_obj = datetime.strptime(giveaway_end, "%d_%m_%Y")
            delta = (date_obj - current_date).days
            with sqlite3.connect('data/db/role/admin.db') as con:
                cur = con.cursor()
                time_app = (cur.execute('SELECT time_app FROM login').fetchone())[0]
            date_obj = datetime.strptime(time_app, "%Y-%m-%d")
            delta_app = (date_obj - current_date).days
            sent_message = await callback_query.message.edit_text (f'👋🏻 <i>Привет, {name}!!! 👋🏻\nРозыгрыш №{number} <b><u>активен</u></b>\nПроводиться в канале <a href="{giveaway_link}">{giveaway_name}</a> \nПосмотреть пост можно тут 👉🏻<a href="{link}">ЖМЯК</a>\nДо конца розыгрыша осталось <b><u>{delta}</u></b> дней\n<b>WebApp будет активно еще <u>{delta_app}</u> дней</b>\nВыбирай нужный пункт</i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            with sqlite3.connect('data/db/role/admin.db') as con:
                cur = con.cursor()
                time_app = (cur.execute('SELECT time_app FROM login').fetchone())[0]
            current_date = datetime.today()
            date_obj = datetime.strptime(time_app, "%Y-%m-%d")
            delta_app = (date_obj - current_date).days
            sent_message = await callback_query.message.edit_text (f"👋🏻 <i>Привет, {name}!!! 👋🏻\n<b>WebApp будет активно еще <u>{delta_app}</u> дней</b>\nВыбирай нужный пункт</i>", parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    

    elif data == "selenium_update":
        async for result in update.update_webapp():
            await bot.send_message(callback_query.from_user.id, result)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("В процессе реализации", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        #async for result in marsh.check_marshrut():
        #    await bot.send_message(callback_query.from_user.id, result)


    elif data == "start_adminbase":
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM admins")
        rows = cur.fetchall()
        con.close()
        response = "<i>Админы бота:</i>\n\n"
        for row in rows:
            response += f"{row[0]}) Имя {row[2]} Ник @{row[3]}\n"
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="➕Добавить➕", callback_data="start_adminbase_plus"))
        board.add(types.InlineKeyboardButton(text="➖Убрать➖", callback_data="start_adminbase_minus"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(2, 1)
        sent_message = await callback_query.message.edit_text(response, parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "start_adminbase_plus":
        await state.set_state(ADMINS.idtg)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        await callback_query.message.edit_text("<i>Вводи ID телеграма нового админа\nЕсли передумал, жми кнопку выше</i>", parse_mode="HTML", reply_markup=board.as_markup())


    elif data == "role_admin":
        await state.update_data(role="admin")
        user_data = await state.get_data()
        idtg = user_data['idtg']
        role = user_data['role']
        await state.clear()
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        cur.execute(f'INSERT INTO admins (idtg, role) VALUES ("{idtg}", "{role}")')
        con.commit()
        con.close()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Записал, пусть новый админ напишет /start</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "role_master":
        await state.update_data(role="master")
        user_data = await state.get_data()
        idtg = user_data['idtg']
        role = user_data['role']
        await state.clear()
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        cur.execute(f'INSERT INTO admins (idtg, role) VALUES ("{idtg}", "{role}")')
        con.commit()
        con.close()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Записал, пусть новый админ напишет /start</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "start_adminbase_minus":
        con = sqlite3.connect('data/db/role/admin.db')
        cur = con.cursor()
        all = cur.execute("SELECT id FROM admins ORDER BY id DESC LIMIT 1")
        all = int((cur.fetchone())[0])
        board = InlineKeyboardBuilder()
        for i in range(1, all+1):
            try:
                nick = cur.execute(f'SELECT nick FROM admins WHERE id = ?', [i]).fetchone()
                idtg = cur.execute(f'SELECT idtg FROM admins WHERE id = ?', [i]).fetchone()
                nick = nick[0]
                idtg = idtg[0]
                board.add(types.InlineKeyboardButton(text=f"{nick}", callback_data=f"adminminus_{idtg}"))
            except:
                pass
        con.close()
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text("<i>Выбери админа, которого надо минусануть\nЕсли передумал, жми отмену</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "start_sos":
        await state.set_state(ADMINS.help)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Тихо! Без паники!\nВ текстовом формате опиши в чем сложность и я постараюсь максимально быстро присоединится.\nНу либо жми отмену, если стесняшка</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "start_notepad":
        con = sqlite3.connect('data/db/notepad/notepad.db')
        cur = con.cursor()
        board = InlineKeyboardBuilder()
        try:
            all = cur.execute("SELECT id FROM note ORDER BY id DESC LIMIT 1")
            all = int((cur.fetchone())[0])
            cur.execute("SELECT * FROM note")
            rows = cur.fetchall()
            for i in range (1, all+1):
                try:
                    text = cur.execute("SELECT text FROM note WHERE id = ?", (i,)).fetchone()
                    text = text[0]
                    board.add(types.InlineKeyboardButton(text=f"{text}", callback_data=f"notepad_{i}"))
                except:
                    pass
            con.close()
        except:
            pass
        con.close()
        board.add(types.InlineKeyboardButton(text="➕Добавить запись➕", callback_data="note_plus"))
        board.add(types.InlineKeyboardButton(text="➖Удалить запись➖", callback_data="note_minus"))
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        board.adjust(*[1] * len(rows), 2, 1)
        sent_message = await callback_query.message.edit_text("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == 'note_plus':
        await state.set_state(ADMINS.text)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Окей, ты захотел оставить инструмент для потомков.\nБудем действовать в несколько этапов:\n1) Для начала краткое описание инструмента (одно - два слова)\n2) Затем мне надо будет ссылку на инструмент\n3) Далее я попрошу ввести полное описание инструмента (ограничений в символах нет)\n\nЕсли передумал - жми отмену\nЕсли не передумал - вводи <b>краткое</b> описание</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "note_minus":
        await state.set_state(ADMINS.minus)
        con = sqlite3.connect('data/db/notepad/notepad.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM note")
        rows = cur.fetchall()
        con.close()
        result = "<i>Записи по номерам:</i>\n\n"
        for row in rows:
            result += f"<u>{row[0]}) {row[4]}</u>\n"
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text(f"{result}<i><b>\nВводи номер записи, которую надо удалить. Либо жми отмена</b></i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway":
        board = InlineKeyboardBuilder()
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            act = "active"
            try:
                exsist = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
            except:
                exsist = None
        if exsist:
            board.add(types.InlineKeyboardButton(text="🏁Завершить активный розыгрыш🏁",  callback_data="giveaway_end"))
        else:
            board.add(types.InlineKeyboardButton(text="▶️ Старт нового розыгрыша", callback_data="giveaway_start"))
        board.add(types.InlineKeyboardButton(text="Отменить все активные розыгрыши",  callback_data="giveaway_stop"))
        board.add(types.InlineKeyboardButton(text="🆘Ручной режим🆘",  callback_data="giveaway_sos"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text("<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_sos":
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="Срандомить победителей", callback_data="giveaway_random"))
        board.add(types.InlineKeyboardButton(text="Просмотр зареганых", callback_data="giveaway_sos_look"))
        board.add(types.InlineKeyboardButton(text="Отправка сообщения от имени бота",  callback_data="giveaway_sos_send"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text("<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_end":
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="❌Нет, я случайно❌", callback_data="ok"))
        await state.set_state(GIVEAWAY.much_win)
        sent_message = await callback_query.message.edit_text("<i>Пора подвести итоги розыгрыша?\n🤔 Мне надо знать, сколько будет победителей.\n <b>Жду число...</b></i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_sos_send":
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="У меня есть эти данные", callback_data="giveaway_manual_send"))
        board.add(types.InlineKeyboardButton(text="Просмотр зареганых", callback_data="giveaway_sos_look"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text("<i>Чтобы отправить сообщение вручную от имени бота мне необходимо:\n<b>idtg</b>\n<b>Name</b>\n<b>Password</b>\nЭти данные можно найти, просмотрев зареганных пользователей, а пароль придется срандомить</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_manual_send":
        await state.set_state(manual_send.idtg)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Жду ввода <b>IDTG</b></i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "manual_send_go":
        manual_data = await state.get_data()
        idtg = manual_data['idtg']
        await state.clear()
        with open(f'data/variables/text/manual_send.txt', "r", encoding="utf-8") as file:
            text = file.read()
        try:
            await bot.send_message(chat_id = idtg, text = text, parse_mode="HTML", disable_web_page_preview=True)
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.edit_text("<i>Сообщение отправлено</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except Exception as e:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.edit_text(f"<i>Ошибка отправки сообщения пользователю:</i>\n{e}", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_sos_look":
        try:
            text = "Зареганные пользователи:\n"
            with open('data/db/giveaway/giveaway_tributes.txt', "w", encoding="utf-8") as file:
                file.write(text)
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                cur.execute("SELECT id, id_tg, us_nick, us_name FROM tributes")
                rows = cur.fetchall()
            for row in rows:
                with open('data/db/giveaway/giveaway_tributes.txt', "a", encoding="utf-8") as file:
                    text = f'IDTG {row[1]}    NICK {row[2]}    NAME {row[3]}\n'
                    file.write(text)
            with open('data/db/giveaway/giveaway_tributes.txt', "r", encoding="utf-8") as file:
                text = file.read()
            max_length: int = 4096
            lines = text.split("\n")  # Разделяем файл на строки
            current_message = ""
            for line in lines:
                # Если добавление новой строки не превысит лимит
                if len(current_message) + len(line) + 1 <= max_length:  # +1 учитывает символ '\n'
                    current_message += line + "\n"
                else:
                    # Если текущее сообщение не пустое, отправляем его
                    if current_message.strip():
                        try:
                            sent_message = await callback_query.message.answer(current_message.strip(), parse_mode="HTML")
                            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
                        except Exception as e:
                            print(f"Ошибка отправки: {e}")
                    current_message = line + "\n"  # Начинаем новое сообщение с текущей строки

            # Отправляем остаток, если он есть
            if current_message.strip():
                sent_message = await callback_query.message.answer(current_message.strip(), parse_mode="HTML")
                asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.answer("Вот все зареганные пользователи без проверки на подписку", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except Exception as e:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.edit_text(f"<i>Возникла ошибка: {e}\n--------------\nПопробуй еще раз, либо пиши в SOS</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_start":
        try:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                exist = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', ["active"]).fetchone())[0]
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.edit_text(f'<i>Наркоман чтоле!\nУже есть АКТИВНЫЙ РОЗЫГРЫШ в <a href="{exist}">канале</a>!</i>', parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            try:
                with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                    cur = con.cursor()
                    cur.execute("DROP TABLE IF EXISTS loser")
                    cur.execute("DROP TABLE IF EXISTS tributes")
                    cur.execute("DROP TABLE IF EXISTS winners")
                    con.commit()
            except Exception as e:
                await callback_query.message.answer(f"<i>Не удалось удалить старую базу розыгрыша\nОшибка {e}</i>", parse_mode="HTML")
            try:
            # Удаление базы винеров
                with sqlite3.connect('data/db/giveaway/winners.db') as con:
                    cur = con.cursor()
                    cur.execute("DROP TABLE IF EXISTS winners")
                    con.commit()
            except Exception as e:
                await callback_query.message.answer(f"<i>Не удалось удалить старую базу винеров\nОшибка {e}</i>", parse_mode="HTML")
            

# Проверяем срок действия
            response = requests.get(
                'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/'.format(
                username=username_app
                ),
                headers={'Authorization': 'Token {token}'.format(token=token_app)}
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml').text
                data = response.json()
                expiry_date = data[0]['expiry']
                time_web = datetime.strptime(f"{expiry_date}", "%Y-%m-%d").date()
                time_now = (datetime.today()).date()
                exp = (time_web - time_now).days

                with sqlite3.connect('data/db/role/admin.db') as con:
                    cur = con.cursor()
                    cur.execute('UPDATE login SET time_app = ?', [time_web])

    # для проверки таска            
    #            response = requests.get(
    #                'https://www.pythonanywhere.com/api/v0/user/{username}/schedule/'.format(
    #                username=username_app
    #                ),
    #                headers={'Authorization': 'Token {token}'.format(token=token_app)}
    #            )
    #            soup = BeautifulSoup(response.text, 'lxml').text
    #            data = response.json()
    #            expiry_date = data[0]['expiry']
    #            time_web = datetime.strptime(f"{expiry_date}", "%Y-%m-%d").date()
    #            time_now = datetime.today()
    #            task_expiry = (time_web - time_now).days
            else:
                exp = 'не удалось обновить'

            con = sqlite3.connect('data/db/giveaway/chan_data.db')
            cur = con.cursor()
            cur.execute("SELECT * FROM channals")
            rows = cur.fetchall()
            con.close()
            board = InlineKeyboardBuilder()
            try:
                for row in rows:
                    board.add(types.InlineKeyboardButton(text=f"{row[2]}", callback_data=f"start_giveaway:{row[1]}"))
                board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
                board.add(types.InlineKeyboardButton(text="➖Удалить канал➖", callback_data="channal_minus"))
                board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
                board.adjust(*[1] * len(rows), 2, 1)
                sent_message = await callback_query.message.edit_text(f"<i><b>WebApp будет активно еще <u>{exp}</u> дней</b>\nВыбирай канал для запуска розыгрыша</i>", parse_mode="HTML", reply_markup=board.as_markup())
                asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
            except:
                board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
                board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
                board.adjust(*[1] * len(rows), 1, 1)
                sent_message = await callback_query.message.edit_text(f"<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
                asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_stop":
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="✅Да", callback_data="giveaway_stop_choise"))
        board.add(types.InlineKeyboardButton(text="❌Нет", callback_data="ok"))
        board.adjust(2)
        sent_message = await callback_query.message.edit_text("<i>Ты выбрал <b>ОТМЕНИТЬ</b> активный розыгрыш по каким то причинам.\n<b>ДАННАЯ ОПЕРАЦИЯ НЕОБРАТИМА</b>\nПродолжить?</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_stop_choise":
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            act = "active"
            name_file = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
        await state.set_state(GIVEAWAY.name_file)
        await state.update_data(name_file=name_file)
        await state.set_state(GIVEAWAY.stop_reason)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Для отмены розыгрыша, необходимо указать причину.\nНапиши, пожалуйста, по какой причине отменяется розыгрыш\n\n<b>ЖДУ</b></i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_stop_go":
        path = 'data/db/giveaway/giveaway.db'
        reason_data = await state.get_data()
        reason = reason_data['stop_reason']
        name_file = reason_data['name_file']
        await state.clear()
        try:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                cur.execute(f'UPDATE giveaways_data SET giveaway_status = ? WHERE giveaway_status = "active" ', ["finish"])
                con.commit()
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            with open(f'data/history/log {name_file}.txt', "a", encoding="utf-8") as f:
                text = f'<b>Розыгрыш отменил</b> {nick}\n<b>Причина:</b> {reason}'
                f = f.write(text)
            sent_message = await callback_query.message.edit_text("<i>Активный розыгрыш отменен\nинформация в историю добавлена</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await callback_query.message.edit_text("<i>Не удалось отменить розыгрыш. Пиши в SOS</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
       

    elif data == "giveaway_random":
        act = "active"
        stop_flag = 0
        result = "Нарандомил:\n"
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            cur.execute(f"DROP TABLE IF EXISTS winners")
            cur.execute(f"DROP TABLE IF EXISTS loser")
            con.commit()
            cur.execute('''
            CREATE TABLE IF NOT EXISTS winners(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    id_tg VARCHAR (20),
                    us_nick VARCHAR (20),
                    us_name VARCHAR (20),
                    password VARCHAR (30),
                    us_ava BLOB
                    )''')
            cur.execute('''
            CREATE TABLE IF NOT EXISTS loser(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    id_tg VARCHAR (20),
                    us_name VARCHAR (20),
                    reason VARCHAR (20)
                    )''')
            con.commit()
            
            all = int((cur.execute('SELECT COUNT (*) FROM tributes').fetchone())[0])
            much_win = int((cur.execute('SELECT giveaway_much_win FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0])
            chan_id = (cur.execute('SELECT chan_id FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
            all = list(range(1, all+1))
            while stop_flag != much_win:
                wins_number = random.sample(all, much_win)
                cur = con.cursor()
                for win in wins_number:
                    idtg = (cur.execute('SELECT id_tg FROM tributes WHERE id = ?', [win]).fetchone())[0]
                    us_nick = (cur.execute('SELECT us_nick FROM tributes WHERE id = ?', [win]).fetchone())[0]
                    us_name = (cur.execute('SELECT us_name FROM tributes WHERE id = ?', [win]).fetchone())[0]
                    podpiska = await bot.get_chat_member(chat_id=chan_id, user_id=idtg)
                    podpiska = podpiska.status
                    if podpiska in ["member", "administrator", "creator"]:
                        if us_nick == "MINUS":
                            cur.execute(f'INSERT INTO loser (id_tg, us_name, reason) VALUES ("{idtg}", "{us_name}", "отсутствует тег")')
                            con.commit()
                            all.remove(win)
                        else:
                            password = ''
                            for x in range(10): #Количество символов (10)
                                password = password + random.choice(list('1234567890abcdefghigklmnopqrstuvyxwzABCDEFGHIGKLMNOPQRSTUVYXWZ!@#$%^&*()'))
                            ava = (cur.execute('SELECT us_ava FROM tributes WHERE id_tg = ?', [idtg]).fetchone())[0]
                            cur.execute(f'UPDATE tributes SET us_nick = ? WHERE id = {win} ', ["WINNER"])
                            cur.execute('INSERT INTO winners (id_tg, us_nick, us_name, password, us_ava) VALUES (?, ?, ?, ?, ?)', (idtg, us_nick, us_name, password, ava))
                            con.commit()
                            all.remove(win)
                            result += f"{win}) Ник - {us_nick}    Имя - {us_name}\n"
                            stop_flag = (cur.execute('SELECT COUNT (*) from winners').fetchone())[0]
                            if stop_flag == much_win:
                                break
                    else: 
                        cur.execute(f'INSERT INTO loser (id_tg, us_name, reason) VALUES ("{idtg}", "{us_name}", "отписался")')
                        con.commit() 
                        all.remove(win)
                
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="✅Ok", callback_data="giveaway_finish"))
        board.add(types.InlineKeyboardButton(text="❌Заново", callback_data="admentest_rename"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(2, 1)
        sent_message = await callback_query.message.answer(f"{result}\n<i>Отправляем пост в канал и сообщения победителям? Эта операция <b>необратима</b>, розыгрыш завершится</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_finish":
        act = "active"
        end = "finish"
        text = f"<b>Барабан крутил</b> {nick}\n<b>Победители :</b>\n"
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            win_date = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0]
            cur.execute('SELECT id, id_tg, us_nick, us_name, password FROM winners')
            rows = cur.fetchall()
        for row in rows:
            text += f"{row[0]}) Ник - {row[2]}, Имя - {row[3]}, Пароль - {row[4]}\n"
            try:
                idtg = int(row[1])
                await bot.send_message(idtg, f"<i>Привет, {row[3]}!\nВы победили в розыгрыше от Firestorm.\nПароль на получение выигрыша</i>\n👉🏻 <b>{row[4]}</b> 👈🏻\n<i>Сообщите его <u>Aorid</u> или <u>Retmex</u> в дискорде и получите свой приз!</i>", parse_mode="HTML")
                text += "сообщение с паролем отправлено\n"
            except Exception as e:
                text += f"сообщение с паролем не отправлено. Ошибка {e}\n"
        with open (f'data/history/log {win_date}.txt', "a", encoding="utf-8") as file:
            file.write(text)
        try:
            loser_text = '<b>Лузера:</b>\n'
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                cur.execute("SELECT * FROM loser")
                rows = cur.fetchall()

            for row in rows:
                loser_text += f'{row[0]}) <b>Idtg</b> - {row[1]}, <b>name</b> - {row[2]}\n<b>Причина</b> - {row[3]}\n'
            with open (f'data/history/log {win_date}.txt', "a", encoding="utf-8") as file:
                file.write(loser_text)
        except Exception as e:
            await callback_query.message.answer(f"<i>Не удалось залогировать базу лузеров\nОшибка {e}</i>", parse_mode="HTML")
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM winners")
            rows = cur.fetchall()

        date = datetime.today()
        date = date.strftime("%d.%m.%Y")

        with sqlite3.connect('data/db/giveaway/winners.db') as con:
            cur = con.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS winners(Id INTEGER PRIMARY KEY AUTOINCREMENT, id_tg VARCHAR (20), us_nick VARCHAR (40), us_name VARCHAR (40), password VARCHAR (20), us_ava BLOB, ava_path VARCHAR (200), giveaway_date VARCHAR (20))')
            for row in rows:
                cur.execute('INSERT INTO winners (id_tg, us_nick, us_name, password, us_ava, giveaway_date) VALUES (?, ?, ?, ?, ?, ?)', (row[1], row[2], row[3], row[4], row[5], date))
            con.commit()
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            cur.execute(f'UPDATE giveaways_data SET admin_end = ? WHERE giveaway_status = "active" ', [nick])
            chan_id = int((cur.execute('SELECT chan_id FROM giveaways_data WHERE giveaway_status = ?', [act]).fetchone())[0])
            cur.execute(f'UPDATE giveaways_data SET giveaway_status = ? WHERE giveaway_status = "active" ', ["finish"])
            con.commit()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.answer(f"<i>Отправка сообщений завершена\nИстория розыгрыша записана\nРозыгрыш полностью завершен</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        scr = FSInputFile("data/variables/post/start_post.jpg")
        with open('data/variables/post/end_post.txt', "r", encoding="utf-8") as f:
            caption = f.read()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="🎁Узнать результат🎁", url='https://t.me/Firestorm_contest_bot'))
        await bot.send_photo(chat_id=chan_id, photo=scr, caption=caption, parse_mode="HTML", reply_markup=board.as_markup())
        
        # Льем базу на WebApp
        api_username = 'firestormwebapp'
        api_token = '2189e082315434ef3a071884a88db47ce912e954'
        remote_path = '/home/firestormwebapp/webapp/winners.db'
        file_path = 'data/db/giveaway/winners.db'
        url = f"https://www.pythonanywhere.com/api/v0/user/{api_username}/files/path{remote_path}"
        headers = {"Authorization": f"Token {api_token}"}
        with open(file_path, "rb") as file:
            file_content = file.read()
        response = requests.post(url, headers=headers, files={"content": file_content})


    elif data == "channal_plus":
        await state.set_state(CHAN.name_chan)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await callback_query.message.edit_text("<i>Вводи <b>имя</b> канала</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "channal_minus":
        con = sqlite3.connect('data/db/giveaway/chan_data.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM channals")
        rows = cur.fetchall()
        con.close()
        board = InlineKeyboardBuilder()
        try:
            for row in rows:
                board.add(types.InlineKeyboardButton(text=f"{row[2]}", callback_data=f"chan_minus:{row[0]}"))
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            board.adjust(1)
            sent_message = await callback_query.message.edit_text(f"<i>Выбирай канал который надо <b><u>УДАЛИТЬ</u></b></i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            board.adjust(1)
            sent_message = await callback_query.message.edit_text(f"<i>Все каналы удалены</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "post_ok":
        giveaway_data = await state.get_data()
        admin_nick = callback_query.from_user.username
        chan_id = int(giveaway_data['chan_id'])
        chan_link = giveaway_data['link']
        chan_name = giveaway_data['name']
        date_end = giveaway_data['date_end']
        await state.clear()
        jpg_post = FSInputFile("data/variables/post/start_post.jpg")
        with open('data/variables/post/start_post.txt', "r", encoding="utf-8") as f:
            text_post = f.read()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="Регистрация", url='https://t.me/Firestorm_contest_bot'))
        msg = await bot.send_photo(chat_id=chan_id, photo=jpg_post, caption=text_post, parse_mode="HTML", reply_markup=board.as_markup())
        msg_id = msg.message_id
        with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
            cur = con.cursor()
            cur.execute(f'INSERT INTO giveaways_data (admin_start, chan_name, chan_id, chan_link, msg_id, giveaway_status, giveaway_end) VALUES ("{admin_nick}", "{chan_name}", "{chan_id}", "{chan_link}", "{msg_id}", "active", "{date_end}")')
            con.commit()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        date_end = datetime.strptime(date_end, "%d_%m_%Y")
        name_file = date_end.strftime("%d_%m_%Y")
        date_end = date_end.strftime("%d.%m.%Y")
        with open(f'data/history/log {name_file}.txt', "w", encoding="utf-8") as f:
            text = f'<b>Дата окончания розыгрыша</b> {date_end}\n<b>Розыгрыш создал</b> {admin_nick}\n'
            f = f.write(text)
        sent_message = await callback_query.message.edit_text(f"<i>Пост улетел, оформление закончено, можно отдыхать до {date_end}\nЖми кнопку</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == 'calendar_start':
        await callback_query.message.answer("Выберите дату:", reply_markup=await SimpleCalendar().start_calendar())


    elif data == 'admentest':
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="Сгенерировать базу участников", callback_data="admentest_bd"))
        board.add(types.InlineKeyboardButton(text="Проверка херни", callback_data="admentest_rename"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text("<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == 'admentest_bd':
        print ("ghjdthrf")


    elif data == "admentest_rename":
        print ("ghjdthrf")




# Ручная отправка сообщения пользователю
@dp.message(manual_send.idtg)
async def manual_send_idtg(message: Message, state: FSMContext):
    await state.update_data(idtg=message.text)
    await message.answer ("<i>Теперь вводи Name</i>", parse_mode="HTML")
    await state.set_state(manual_send.name)
@dp.message(manual_send.name)
async def manual_send_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer ("<i>Теперь вводи Password</i>", parse_mode="HTML")
    await state.set_state(manual_send.password)
@dp.message(manual_send.password)
async def manual_send_name(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    manual_data = await state.get_data()
    
    try:
        name = manual_data['name']
        password = manual_data['password']
        board = InlineKeyboardBuilder()
        with open(f'data/variables/text/manual_send.txt', "w", encoding="utf-8") as file:
            text = f'<i>Приветствую, {name}!!! 👋🏻\nВы победили в розыгрыше от <b><a href="https://firestorm-servers.com/ru">Firestorm</a></b> 🥳\nПароль для получение выигрыша \n👉🏻 {password} 👈🏻\nСообщите его в личные сообщения дискорд <u>Aorid</u> либо <u>Retmex</u> и получите свой приз 🏆 !</i>'
            file.write(text)
        board.add(types.InlineKeyboardButton(text="✅Отправляем✅", callback_data="manual_send_go"))
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await message.answer (f'<i>Проверка сообщения перед отправкой:\nПриветствую, {name}!!! 👋🏻\nВы победили в розыгрыше от <b><a href="https://firestorm-servers.com/ru">Firestorm</a></b> 🥳\nПароль для получение выигрыша \n👉🏻 {password} 👈🏻\nСообщите его в личные сообщения дискорд <u>Aorid</u> либо <u>Retmex</u> и получите свой приз 🏆 !</i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    except:
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await message.answer (f"<i>Ошибка в введенных данных (скорей всего idtg) </i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Определение количества победителей
@dp.message(GIVEAWAY.much_win)
async def much_win(message: Message, state: FSMContext):
    await state.update_data(much_win=message.text)
    win_data = await state.get_data()
    await state.clear()
    try:
        much_win = int(win_data['much_win'])
        act = 'active'
        if much_win > 0:
            with sqlite3.connect('data/db/giveaway/giveaway.db') as con:
                cur = con.cursor()
                cur.execute(f'UPDATE giveaways_data SET giveaway_much_win = ? WHERE giveaway_status = "active" ', [much_win])
                con.commit()
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="✅Далее", callback_data="giveaway_random"))
            board.add(types.InlineKeyboardButton(text="❌Передумал", callback_data="ok"))
            sent_message = await message.answer(f"<i>👌 Победителей будет <u>{much_win}</u>\nДля продолжения жми кнопку</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        else:
            await state.set_state(GIVEAWAY.much_win)
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await message.answer(f"<i><b>Как ты себе представляешь {much_win} победителей??\nВводи коректное ЦЕЛОЕ число, или жми отмену</b></i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    except Exception as e:
        await state.set_state(GIVEAWAY.much_win)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        sent_message = await message.answer(f"<i><b>Шуточки за 300??</b>\nВводи коректное ЦЕЛОЕ число, или жми отмену</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))



# Разбивка сообщения, максимум 4096 знаков
async def split_message(text: str, max_length: int = 4096) -> list[str]:
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

        
@dp.message(GIVEAWAY.stop_reason)
async def stop(message: Message, state: FSMContext):
    await state.update_data(stop_reason=message.text)
    board = InlineKeyboardBuilder()
    board.add(types.InlineKeyboardButton(text="✅Да, я уверен", callback_data="giveaway_stop_go"))
    board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    board.adjust(1)
    sent_message = await message.answer("<i>Причину принял, но спрошу еще раз:\nТочно отменить активный розыгрыш???</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

# Готовим пост в канал для розыгрыша
@dp.message(GIVEAWAY.post)
async def giveaway_post(message: Message, state: FSMContext):
    if message.caption:
        photo = message.photo[-1]  # Берем фото с самым высоким разрешением
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        download_path = os.path.join('data/variables/post', "start_post.jpg")
        await bot.download_file(file_path, destination=download_path)

        description = message.html_text
        description_path = os.path.join('data/variables/post', "start_post.txt")
        with open(description_path, "w", encoding="utf-8") as f:
            f.write(description)
        with open(description_path, "r", encoding="utf-8") as f:
            text_post = f.read()
        jpg_post = FSInputFile("data/variables/post/start_post.jpg")

        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="✅Отправить", callback_data="post_ok"))
        board.add(types.InlineKeyboardButton(text="❌Переделать", callback_data="giveaway_start"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(2, 1)
        sent_message = await bot.send_photo(message.from_user.id, photo=jpg_post, caption=f"{text_post}", parse_mode="HTML")
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

        sent_message = await message.answer("<i>👆👆👆👆👆👆👆\n\nВот так выглядит твой пост.\nЕсли всё хорошо - жми <b>Отправить</b> и пост полетит в канал</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

# Вносим канал в базу данных
@dp.message(CHAN.name_chan)
async def name_chan(message: Message, state: FSMContext):
    await state.update_data(name_chan=message.text)
    sent_message = await message.answer("<i>Теперь мне надо <b>ID канала</b>\nID канала состоит из цифр, узнать его можно, например, у @LeadConverterToolkitBot</i>", parse_mode="HTML")
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    await state.set_state(CHAN.id_chan)
@dp.message(CHAN.id_chan)
async def id_chan(message: Message, state: FSMContext):
    await state.update_data(id_chan=message.text)
    sent_message = await message.answer("<i>Отлично, осталось внести ссылку на канал\nЖду</i>", parse_mode="HTML")
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    await state.set_state(CHAN.link_chan)
@dp.message(CHAN.link_chan)
async def link_chan(message: Message, state: FSMContext):
    await state.update_data(link_chan=message.text)
    chan_data = await state.get_data()
    name = chan_data['name_chan']
    id_chan = chan_data['id_chan']
    link = chan_data['link_chan']
    await state.clear()
    con = sqlite3.connect('data/db/giveaway/chan_data.db')
    cur = con.cursor()
    cur.execute(f'INSERT INTO channals (id_chan, name, link) VALUES ("{id_chan}", "{name}", "{link}")')
    con.commit()
    con.close()
    con = sqlite3.connect('data/db/giveaway/chan_data.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM channals")
    rows = cur.fetchall()
    con.close()
    board = InlineKeyboardBuilder()
    try:
        for row in rows:
            board.add(types.InlineKeyboardButton(text=f"{row[2]}", callback_data=f"giveaway:{row[0]}"))
        board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
        board.add(types.InlineKeyboardButton(text="➖Удалить канал➖", callback_data="channal_minus"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(*[1] * len(rows), 2, 1)
        sent_message = await message.answer(f"<i>Выбирай канал для запуска розыгрыша</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    except:
        board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
        board.add(types.InlineKeyboardButton(text="➖Удалить канал➖", callback_data="channal_minus"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(*[1] * len(rows), 2, 1)
        sent_message = await message.answer(f"<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Инстументы для потомков
@dp.message(ADMINS.text)
async def note_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    sent_message = await message.answer("<i>Теперь дай ссылку на сайт</i>", parse_mode="HTML")
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    await state.set_state(ADMINS.link)
@dp.message(ADMINS.link)
async def note_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    sent_message = await message.answer("<i>Осталось описать, что можно делать с помощью этого сайта</i>", parse_mode="HTML")
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    await state.set_state(ADMINS.desc)
@dp.message(ADMINS.desc)
async def note_link(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    note_data = await state.get_data()
    admin_nick = message.from_user.username
    link = note_data['link']
    desc = note_data['desc']
    text = note_data['text']
    await state.clear()
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    cur.execute(f'INSERT INTO note (admin_nick, link, desc, text) VALUES ("{admin_nick}", "{link}", "{desc}", "{text}")')
    con.commit()
    cur.close()
    con.close()
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    all = cur.execute("SELECT id FROM note ORDER BY id DESC LIMIT 1")
    all = int((cur.fetchone())[0])
    cur.execute("SELECT * FROM note")
    rows = cur.fetchall()
    board = InlineKeyboardBuilder()
    for i in range (1, all+1):
        try:
            text = cur.execute("SELECT text FROM note WHERE id = ?", (i,)).fetchone()
            text = text[0]
            board.add(types.InlineKeyboardButton(text=f"{text}", callback_data=f"notepad_{i}"))
        except:
            pass
    con.close()
    board.add(types.InlineKeyboardButton(text="➕Добавить запись➕", callback_data="note_plus"))
    board.add(types.InlineKeyboardButton(text="➖Удалить запись➖", callback_data="note_minus"))
    board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
    board.adjust(*[1] * len(rows), 2, 1)
    sent_message = await message.answer("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


@dp.message(ADMINS.minus)                     
async def note_minus(message: Message, state: FSMContext):
    await state.update_data(note_minus=message.html_text)
    note_data = await state.get_data()
    number = note_data['note_minus']
    await state.clear()
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    cur.execute("DELETE FROM note WHERE id = ?", (number,))    
    con.commit()
    con.close()
    con = sqlite3.connect('data/db/notepad/notepad.db')
    cur = con.cursor()
    all = cur.execute("SELECT id FROM note ORDER BY id DESC LIMIT 1")
    all = int((cur.fetchone())[0])
    board = InlineKeyboardBuilder()
    cur.execute("SELECT * FROM note")
    rows = cur.fetchall()
    for i in range (1, all+1):
        try:
            text = cur.execute("SELECT text FROM note WHERE id = ?", (i,)).fetchone()
            text = text[0]
            board.add(types.InlineKeyboardButton(text=f"{text}", callback_data=f"notepad_{i}"))
        except:
            pass
    con.close()
    board.add(types.InlineKeyboardButton(text="➕Добавить запись➕", callback_data="note_plus"))
    board.add(types.InlineKeyboardButton(text="➖Удалить запись➖", callback_data="note_minus"))
    board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
    board.adjust(*[1] * len(rows), 2, 1)
    sent_message = await message.answer("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# SOS админу
@dp.message(ADMINS.help)
async def admin_plus(message: Message, state: FSMContext):
    await state.update_data(help=message.html_text)
    nick = message.from_user.username
    user_data = await state.get_data()
    with open("data/variables/text/SOS.txt", "w", encoding="utf-8") as file:
        file.write(f"<b>Админ:</b> @{nick}\n")
        file.write(f"<b>Проблема:</b> {user_data['help']}\n")
    with open("data/variables/text/SOS.txt", "r", encoding="utf-8") as file:
        text_sos = file.read()
        try:
            await bot.send_message(chat_id=master_id, text=text_sos, parse_mode="HTML")
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await message.answer("<i>😂Ваше обращение принято, ожидайте😂</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

        except:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            sent_message = await message.answer("<i>😂Чот хозяин потерялся\nТак что если какие-то проблемы - решай😂</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Добавление админа в БД
@dp.message(ADMINS.idtg)
async def admin_plus(message: Message, state: FSMContext):
    await state.update_data(idtg=message.text)
    board = InlineKeyboardBuilder()
    board.add(types.InlineKeyboardButton(text="admin", callback_data="role_admin"))
    board.add(types.InlineKeyboardButton(text="master", callback_data="role_master"))
    sent_message = await message.answer("<i>Выбери роль</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Сортировка в браузере
def get_sorted_items(path: str):
    files = []
    for filename in os.listdir(HISTORY_DIR):
        filepath = os.path.join(HISTORY_DIR, filename)
        if os.path.isfile(filepath):
            mtime = os.path.getmtime(filepath)
            files.append({
                'name': filename,
                'path': filepath,
                'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'mtime': mtime
            })
    
    
    # Сортируем по дате изменения (сначала новые)
    files.sort(key=lambda x: x['mtime'])
    return files


# Функция для отображения содержимого директории
async def list_directory(message: types.Message, path: str):
    items = get_sorted_items(HISTORY_DIR)
    files = items
    MAX_FILES = 12
    if len(files) > MAX_FILES:
        # Получаем список файлов для удаления (самые старые)
        files_to_delete = files[MAX_FILES:]
        for file in files_to_delete:
            try:
                os.remove(file['path'])
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
    files = items
    board = InlineKeyboardBuilder()
    for file in files:
        button_text = (file['name']).split(" ", 1)[1]
        filename = button_text
        button_text = button_text.split(".", 1)[0]
        board.add(types.InlineKeyboardButton(text=button_text, callback_data=f"log:{filename}"))
    board.row(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    board.adjust(*[3] * len(files), 1)
    sent_message = await message.edit_text("<i>Когда производился розыгрыш?\nВыбери дату окончания</i>", parse_mode="HTML", reply_markup=board.as_markup())
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


# Проверка админ/юзер
def is_user_admin(user_id: int):
    con = sqlite3.connect('data/db/role/admin.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM admins WHERE idtg = ?", (user_id,))
    user = cur.fetchone()
    con.close()
    return user is not None

# Проверка роли в БД
def role_in_db(user_id: str):
    with sqlite3.connect('data/db/role/admin.db') as con:
        cur = con.cursor()
        cur.execute('SELECT role FROM admins WHERE idtg = ?', [user_id])
        result = cur.fetchone()
    return result[0] if result else None

# Удаление сообщения после задержки
async def delete_message_after_delay(chat_id: int, message_id: int, delay: int = 600):
    await asyncio.sleep(delay)  # Задержка в секундах
    await bot.delete_message(chat_id, message_id)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())