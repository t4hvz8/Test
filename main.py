#        random_sticker = random.choice(stickers_hi)
#        await bot.send_sticker(message.chat.id, random_sticker)
#       900865796
# создать pip freeze > requirements.txt
# установить pip install -r requirements.txt



import sqlite3
import datetime
import os
import asyncio
import random

import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message


from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery

from aiogram.types.input_file import FSInputFile

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
            board.add(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.add(types.InlineKeyboardButton(text="Управление розыгрышем", callback_data="start_giveaway"))
        board.add(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.add(types.InlineKeyboardButton(text="Записная книжка", callback_data="start_notepad"))
        board.add(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        board.adjust(1)
        await message.answer (f"👋🏻 <i>Привет, {name}!!! 👋🏻\nВыбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
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
        board.adjust(1)
        await callback_query.message.edit_text("<i>Админ удален</i>", parse_mode="HTML", reply_markup=board.as_markup())
    except:
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        board.adjust(1)
        await callback_query.message.edit_text("<i>Ошибка при удалении админа</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
    board.adjust(3)
    board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    await callback_query.message.edit_text(f"{winner_text}\n--------------------\n<i>Когда производился розыгрыш?\nВыбери дату окончания</i>", parse_mode="HTML", reply_markup=board.as_markup())

# Обработчик чтения записной книжки
@dp.callback_query(lambda c: c.data.startswith("notepad_"))
async def note_read(callback_query: types.CallbackQuery):
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
    board.add(types.InlineKeyboardButton(text="➕Добавить запись➕", callback_data="note_pad_plus"))
    board.add(types.InlineKeyboardButton(text="➖Удалить запись➖", callback_data="notepad_minus"))
    board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
    board.adjust(1)
    await callback_query.message.edit_text(f"<i>{text_base}\n{link}\n{desc}\n Добавил <b>@{nick}</b></i>", parse_mode="HTML", disable_web_page_preview=True, reply_markup=board.as_markup())

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
        await state.clear()
        board = InlineKeyboardBuilder()
        if role  == 'master':
            board.add(types.InlineKeyboardButton(text="Работа с базой админов", callback_data="start_adminbase"))
        board.add(types.InlineKeyboardButton(text="Управление розыгрышем", callback_data="start_giveaway"))
        board.add(types.InlineKeyboardButton(text="История розыгрышей", callback_data="start_history"))
        board.add(types.InlineKeyboardButton(text="Записная книжка", callback_data="start_notepad"))
        board.add(types.InlineKeyboardButton(text="❗️HELP❗️SOS❗️", callback_data="start_sos"))
        board.adjust(1)
        await callback_query.message.edit_text(f"👋🏻 <i>Привет, {nick}!!! 👋🏻\nВыбирай нужный пункт</i>", parse_mode="HTML", reply_markup=board.as_markup())
    
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
        await callback_query.message.edit_text(response, parse_mode="HTML", reply_markup=board.as_markup())

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
        await callback_query.message.edit_text("<i>Записал, пусть новый админ напишет /start</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
        await callback_query.message.edit_text("<i>Записал, пусть новый админ напишет /start</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
        await callback_query.message.edit_text("<i>Выбери админа, которого надо минусануть\nЕсли передумал, жми отмену</i>", parse_mode="HTML", reply_markup=board.as_markup())

    elif data == "start_sos":
        await state.set_state(ADMINS.help)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️Отмена↩️", callback_data="ok"))
        await callback_query.message.edit_text("<i>Тихо! Без паники!\nВ текстовом формате опиши в чем сложность и я постараюсь максимально быстро присоединится.\nНу либо жми отмену, если стесняшка</i>", parse_mode="HTML", reply_markup=board.as_markup())

    elif data == "start_notepad":
        con = sqlite3.connect('data/db/notepad/notepad.db')
        cur = con.cursor()
        board = InlineKeyboardBuilder()
        try:
            all = cur.execute("SELECT id FROM note ORDER BY id DESC LIMIT 1")
            all = int((cur.fetchone())[0])
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
        board.adjust(1)
        await callback_query.message.edit_text("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())

    elif data == 'note_plus':
        await state.set_state(ADMINS.text)
        board = InlineKeyboardBuilder()
        board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
        await callback_query.message.edit_text("<i>Окей, ты захотел оставить инструмент для потомков.\nБудем действовать в несколько этапов:\n1) Для начала краткое описание инструмента (одно - два слова)\n2) Затем мне надо будет ссылку на инструмент\n3) Далее я попрошу ввести полное описание инструмента (ограничений в символах нет)\n\nЕсли передумал - жми отмену\nЕсли не передумал - вводи <b>краткое</b> описание</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
        await callback_query.message.edit_text(f"{result}<i><b>\nВводи номер записи, которую надо удалить. Либо жми отмена</b></i>", parse_mode="HTML", reply_markup=board.as_markup())

# Инстументы для потомков
@dp.message(ADMINS.text)
async def note_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("<i>Теперь дай ссылку на сайт</i>", parse_mode="HTML")
    await state.set_state(ADMINS.link)
@dp.message(ADMINS.link)
async def note_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer("<i>Осталось описать, что можно делать с помощью этого сайта</i>", parse_mode="HTML")
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
    board.adjust(1)
    await message.answer("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
    board.adjust(1)
    await message.answer("<i><b>Firestorm</b> должен существовать всегда.\nПоэтому нам необходимо оставить накопленные инструменты для потомков.\nВыбери пункт, который тебе интересен</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
            await message.answer("<i>😂Ваше обращение принято, ожидайте😂</i>", parse_mode="HTML", reply_markup=board.as_markup())
        except:
            board = InlineKeyboardBuilder()
            board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
            await message.answer("<i>😂Чот хозяин потерялся\nТак что если какие-то проблемы - решай😂</i>", parse_mode="HTML", reply_markup=board.as_markup())

# Добавление админа в БД
@dp.message(ADMINS.idtg)
async def admin_plus(message: Message, state: FSMContext):
    await state.update_data(idtg=message.text)
    board = InlineKeyboardBuilder()
    board.add(types.InlineKeyboardButton(text="admin", callback_data="role_admin"))
    board.add(types.InlineKeyboardButton(text="master", callback_data="role_master"))
    await message.answer("<i>Выбери роль</i>", parse_mode="HTML", reply_markup=board.as_markup())

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
        print (button_text)
        board.add(types.InlineKeyboardButton(text=button_text, callback_data=f"winners:{file}"))
    board.adjust(3)
    board.add(types.InlineKeyboardButton(text="↪️В начало↩️", callback_data="ok"))
    await message.edit_text("<i>Когда производился розыгрыш?\nВыбери дату окончания</i>", parse_mode="HTML", reply_markup=board.as_markup())

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

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())