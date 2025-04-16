import win32com.client


import pyautogui
import win32com.client as comclt
import sqlite3


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


async def update_webapp():
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-error")
    options.add_argument("--ignore-ssl-errors")
    driver=webdriver.Chrome(options=options)

    yield "Пробуем продлить наш WebApp"

    with sqlite3.connect('data/db/role/admin.db') as con:
        cur = con.cursor()
        login_app = (cur.execute('SELECT login_app FROM login ').fetchone())[0]
        password_app = (cur.execute('SELECT password_app FROM login ').fetchone())[0]
    print (login_app, password_app)
    
    url_get = 'https://www.pythonanywhere.com/login/'
    driver.get(url_get)

    login_form = driver.find_element(By.XPATH, '//*[@id="id_auth-username"]')
    login_form.send_keys(login_app)
        
    pass_form = driver.find_element(By.XPATH, '//*[@id="id_auth-password"]')
    pass_form.send_keys(password_app)
    pass_form.send_keys(Keys.ENTER)

    yield "Авторизация прошла, жди"
    
    url_get = 'https://www.pythonanywhere.com/user/firestormwebapp/webapps/#tab_id_firestormwebapp_pythonanywhere_com'
    driver.get(url_get)
    
    try:
        button = driver.find_element(By.XPATH, '//*[@id="id_firestormwebapp_pythonanywhere_com"]/div[6]/div/div/div/form/input[2]')
        button.click()
        yield "Обновил"
    except Exception as e:
        yield f"Обновление не удалось\nОшибка {e}"
    
    finally:
        driver.close()
        driver.quit()