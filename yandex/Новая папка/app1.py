from flask import Flask, render_template, request, redirect, url_for, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telethon.sync import TelegramClient
import pandas as pd
import os
import asyncio
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask приложение
app = Flask(__name__)
app.secret_key = 'your_unique_secret_key_here'

# Пути и глобальные переменные
REQUEST_FILE = "request.txt"
SEARCH_RESULTS_FILE = "search_results.txt"
SEARCH_RESULTS_XLSX = "search_results.xlsx"
client = None  # Telegram клиент


# Функция парсинга с помощью Selenium
def run_yandex_parser(query):
    try:
        logging.info(f"Запуск парсинга с запросом: {query}")
        with open(REQUEST_FILE, "w", encoding="utf-8") as file:
            file.write(query)

        # Инициализация браузера
        browser = webdriver.Firefox()
        browser.get("https://yandex.ru/maps/")

        # Ввод запроса
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))
        search_input = browser.find_element(By.XPATH, '//input[@type="text"]')
        search_input.send_keys(query)
        search_input.send_keys(Keys.RETURN)
        time.sleep(4)

        # Обработка результатов
        results = []
        business_elements = browser.find_elements(By.CLASS_NAME, 'search-business-snippet-view__title')
        for el in business_elements:
            results.append(el.text)

        # Сохранение результатов
        with open(SEARCH_RESULTS_FILE, "w", encoding="utf-8") as txt_file:
            txt_file.write("\n".join(results))
        pd.DataFrame(results, columns=["Название"]).to_excel(SEARCH_RESULTS_XLSX, index=False)
        logging.info("Результаты успешно сохранены.")

        browser.quit()
        return "Данные успешно собраны!"
    except Exception as e:
        logging.error(f"Ошибка при выполнении парсинга: {e}")
        return f"Ошибка: {e}"


# Функции Telegram
async def authorize_telegram(phone_number, api_id, api_hash):
    """Авторизация в Telegram."""
    global client
    client = TelegramClient(f"{api_id[:10]}.session", api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        result = await client.send_code_request(phone_number)
        session['phone_code_hash'] = result.phone_code_hash
        logging.info("Код подтверждения отправлен.")
        return True
    return False


async def send_messages(user_data, message_text):
    """Отправка сообщений пользователям Telegram."""
    for user in user_data:
        username = user.get("Username", "Нет username")
        if username != "Нет username":
            try:
                await client.send_message(username, message_text)
                logging.info(f"Сообщение отправлено пользователю {username}")
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение пользователю {username}: {e}")


# Маршруты Flask
@app.route("/")
def index():
    """Главная страница приложения."""
    return render_template("index.html")


@app.route("/run_parser", methods=["POST"])
def run_parser():
    """Запуск парсинга."""
    query = request.form.get("query", "").strip()
    if not query:
        return "Ошибка: запрос пустой!", 400
    return run_yandex_parser(query)


@app.route("/authorize_telegram", methods=["POST"])
def authorize():
    """Авторизация в Telegram."""
    phone_number = request.form.get("phone_number", "").strip()
    api_id = request.form.get("api_id", "").strip()
    api_hash = request.form.get("api_hash", "").strip()
    if not (phone_number and api_id and api_hash):
        return "Ошибка: Все поля обязательны!", 400
    asyncio.run(authorize_telegram(phone_number, api_id, api_hash))
    return "Авторизация запущена. Проверьте ваш Telegram."


@app.route("/send_messages", methods=["POST"])
def send_msgs():
    """Отправка сообщений."""
    message = request.form.get("message", "").strip()
    if not message:
        return "Ошибка: сообщение не может быть пустым!", 400
    user_data = [{"Username": "example_username"}]  # Пример данных
    asyncio.run(send_messages(user_data, message))
    return "Сообщения отправлены."


if __name__ == "__main__":
    app.run(debug=True)
