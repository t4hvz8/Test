#        random_sticker = random.choice(stickers_hi)
#        await bot.send_sticker(message.chat.id, random_sticker)
#       900865796
# создать pip freeze > requirements.txt
# установить pip install -r requirements.txt
#.row - с новой строки  .add добавляет в строку (по умолчанию 3)




import sqlite3
import os
import asyncio
import random

from datetime import datetime, timedelta

import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message


from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData

from aiogram.types.input_file import FSInputFile

from aiogram_calendar import SimpleCalendarCallback, SimpleCalendar

from config import *
from stikers import *


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
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.chat.first_name
    nick = message.from_user.username
    
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
            board.row(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.row(types.InlineKeyboardButton(text="Управление розыгрышем", callback_data="giveaway"))
        board.row(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.row(types.InlineKeyboardButton(text="Инструкция", callback_data="start_notepad"))
        board.row(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        #board.row(types.InlineKeyboardButton(text="Календарь", callback_data="calendar_start"))
        board.adjust(1)
        try:
            con = sqlite3.connect('data/db/giveaway/giveaway.db')
            cur = con.cursor()
            giveaway_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_msg = (cur.execute('SELECT msg_id FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            con.close()
            link = (f'{giveaway_link}' + '/' + f'{giveaway_msg}')
            current_date = datetime.today()
            date_obj = datetime.strptime(giveaway_end, "%d.%m.%Y")
            delta = (date_obj - current_date).days
            sent_message = await message.answer (f'👋🏻 <i>Привет, {name}!!! 👋🏻\nСейчас активен розыгрыш в канале <a href="{giveaway_link}">{giveaway_name}</a> \nПосмотреть пост можно тут 👉🏻<a href="{link}">ЖМЯК</a>\nДо конца розыгрыша осталось <b><u>{delta}</u></b> дней\nВыбирай нужный пункт</i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            sent_message = await message.answer (f"👋🏻 <i>Привет, {name}!!! 👋🏻\nВыбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    
    
    
    
    else:
        await message.answer (f"👋🏻 Привет, {name}!!! 👋🏻\nТы не админ и тебе тут делать нечего", parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "start_history")
async def process_browser(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await list_directory(callback_query.message, HISTORY_DIR)
    await callback_query.answer()

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
@dp.callback_query(lambda c: c.data.startswith("winners:"))
async def winners(callback_query: types.CallbackQuery):
    await callback_query.answer()
    file_path = callback_query.data.split(":", 1)[1]
    file_path = f"{HISTORY_DIR}" + "/" + f"{file_path}"
    with open (file_path, 'r', encoding="utf-8") as file:
        winner_text = file.read()
    items = get_sorted_items(HISTORY_DIR)
    board = InlineKeyboardBuilder()
    files = items
    for file in files:
        button_text = file.split(" ", 1)[1]
        button_text = button_text.split(".", 1)[0]
        board.add(types.InlineKeyboardButton(text=button_text, callback_data=f"winners:{file}"))
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
    con = sqlite3.connect('data/db/giveaway/giveaway.db')
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
        CREATE TABLE IF NOT EXISTS check_tributes(
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
                podpis VARCHAR (20),
                us_ava BLOB
                )''') 
    
    con.commit()
    cur.close()
    con.close()

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
    board = InlineKeyboardBuilder()
    board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    await state.set_state(GIVEAWAY.post)
    sent_message = await callback_query.message.edit_text(f'<i>Театр начинается с вешалки, а конкурс - с анонса\nТы решил запустить конкурс в канале <a href="{link_chan}">{text}</a>\nДля этого пришли мне пост, которым ты запустишь конкурс (присылать фото вместе с описанием, форматирование текста поддерживается).\n\n<b>ЖДУ ПОСТ</b></i>', parse_mode="HTML", disable_web_page_preview=True)
    asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        giveaway_end = date.strftime("%d.%m.%Y")
        con = sqlite3.connect('data/db/giveaway/giveaway.db')
        cur = con.cursor()
        cur.execute('UPDATE giveaways_data SET giveaway_end = ? WHERE giveaway_status = "active"', [giveaway_end])
        con.commit()
        con.close()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        current_date = datetime.now()

        await callback_query.message.edit_text(f'<i>Фиксирую дату окончания: <u>{date.strftime("%d.%m.%Y")}</u>\nРозыгрыш запущен, можно отдыхать</i>', parse_mode="HTML", reply_markup=board.as_markup())



# Общий обработчик нажатий на кнопки
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    role = role_in_db(user_id)
    callback_data = callback_query.data
    nick = callback_query.from_user.username
    logging.info(f"Юзер {nick} запрос: {callback_data}")
    data = callback_query.data
    await callback_query.answer()

    if data == "ok":
        name = callback_query.from_user.username
        await state.clear()
        board = InlineKeyboardBuilder()
        if role  == 'master':
            board.add(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.add(types.InlineKeyboardButton(text="Управление розыгрышем", callback_data="giveaway"))
        board.add(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.add(types.InlineKeyboardButton(text="Инструменты", callback_data="start_notepad"))
        board.add(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        #board.row(types.InlineKeyboardButton(text="Проверка", callback_data="calendar_start"))
        board.adjust(1)
        try:
            con = sqlite3.connect('data/db/giveaway/giveaway.db')
            cur = con.cursor()
            giveaway_link = (cur.execute('SELECT chan_link FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_name = (cur.execute('SELECT chan_name FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_msg = (cur.execute('SELECT msg_id FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
            con.close()
            link = (f'{giveaway_link}' + '/' + f'{giveaway_msg}')
            current_date = datetime.today()
            date_obj = datetime.strptime(giveaway_end, "%d.%m.%Y")
            delta = (date_obj - current_date).days
            sent_message = await callback_query.message.edit_text (f'👋🏻 <i>Привет, {name}!!! 👋🏻\nСейчас активен розыгрыш в канале <a href="{giveaway_link}">{giveaway_name}</a> \nПосмотреть пост можно тут 👉🏻<a href="{link}">ЖМЯК</a>\nДо конца розыгрыша осталось <b><u>{delta}</u></b> дней\nВыбирай нужный пункт</i>', parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
        except:
            sent_message = await callback_query.message.edit_text(f"👋🏻 <i>Привет, {nick}!!! 👋🏻\nВыбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))
    
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
        board.add(types.InlineKeyboardButton(text="Старт нового розыгрыша", callback_data="giveaway_start"))
        board.add(types.InlineKeyboardButton(text="Завершить активный розыгрыш",  callback_data="giveaway_end"))
        board.add(types.InlineKeyboardButton(text="Отменить все активные розыгрыши",  callback_data="giveaway_stop"))
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        sent_message = await callback_query.message.edit_text(f"<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == "giveaway_start":
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
            sent_message = await callback_query.message.edit_text(f"<i>Выбирай канал для запуска розыгрыша</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))

        except:
            board.add(types.InlineKeyboardButton(text="➕Добавить канал➕", callback_data="channal_plus"))
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            board.adjust(*[1] * len(rows), 1, 1)
            sent_message = await callback_query.message.edit_text(f"<i>Выбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
            asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


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
        await state.clear()
        jpg_post = FSInputFile("data/variables/post/start_post.jpg")
        with open('data/variables/post/start_post.txt', "r", encoding="utf-8") as f:
            text_post = f.read()
        con = sqlite3.connect('data/db/giveaway/giveaway.db')
        cur = con.cursor()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text=f"Регистрация", url='https://t.me/Charcon_bot'))
        msg = await bot.send_photo(chat_id=chan_id, photo=jpg_post, caption=text_post, parse_mode="HTML", reply_markup=board.as_markup())
        msg_id = msg.message_id
        con = sqlite3.connect('data/db/giveaway/giveaway.db')
        cur = con.cursor()
        cur.execute(f'INSERT INTO giveaways_data (admin_start, chan_name, chan_id, chan_link, msg_id, giveaway_status) VALUES ("{admin_nick}", "{chan_name}", "{chan_id}", "{chan_link}", "{msg_id}", "active")')
        con.commit()
        con.close()
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="📆Продолжить📆", callback_data="calendar_start"))
        sent_message = await callback_query.message.edit_text("<i>Пост улетел, осталось выбрать дату окончания розыгрыша\nЖми кнопку</i>", parse_mode="HTML", reply_markup=board.as_markup())
        asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id))


    elif data == 'calendar_start':
        con = sqlite3.connect('data/db/giveaway/giveaway.db')
        cur = con.cursor()
        giveaway_end = (cur.execute('SELECT giveaway_end FROM giveaways_data WHERE giveaway_status = ?', ['active']).fetchone())[0]
        con.close()
        current_date = datetime.today()
        date_obj = datetime.strptime(giveaway_end, "%d.%m.%Y")
        delta = (date_obj - current_date).days
        print (delta)


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
    items = os.listdir(path)
    items_with_time = [(item, os.path.getctime(os.path.join(path, item))) for item in items]
    # Сортировка по времени создания (от старых к новым)
    items_with_time.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in items_with_time]

# Функция для отображения содержимого директории
async def list_directory(message: types.Message, path: str):
    items = get_sorted_items(HISTORY_DIR)
    board = InlineKeyboardBuilder()
    files = items
    for file in files:
        button_text = file.split(" ", 1)[1]
        button_text = button_text.split(".", 1)[0]
        board.add(types.InlineKeyboardButton(text=button_text, callback_data=f"winners:{file}"))
    board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
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
    con = sqlite3.connect('data/db/role/admin.db')
    cur = con.cursor()
    cur.execute('SELECT role FROM admins WHERE idtg = ?', [user_id])
    result = cur.fetchone()
    cur.close()
    con.close()
    return result[0] if result else None

# Удаление сообщения после задержки
async def delete_message_after_delay(chat_id: int, message_id: int, delay: int = 300):
    await asyncio.sleep(delay)  # Задержка в секундах
    await bot.delete_message(chat_id, message_id)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())