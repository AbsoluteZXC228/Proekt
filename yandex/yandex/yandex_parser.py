from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к файлу с запросом
REQUEST_FILE = "request.txt"

# Чтение запроса из файла
if not os.path.exists(REQUEST_FILE):
    print(f"Ошибка: файл {REQUEST_FILE} не найден.")
    exit()

with open(REQUEST_FILE, "r", encoding="utf-8") as file:
    search_query = file.read().strip()

if not search_query:
    print("Ошибка: файл запроса пустой.")
    exit()

print(f"Запрос для поиска: {search_query}")

# Инициализация браузера
try:
    browser = webdriver.Firefox()
    logging.info("Браузер открыт.")
except Exception as e:
    logging.error(f"Ошибка при открытии браузера: {e}")
    exit()

try:
    browser.get("https://yandex.ru/maps/")
    logging.info("Открыта страница Яндекс.Карт.")
except Exception as e:
    logging.error(f"Ошибка при загрузке страницы: {e}")
    browser.quit()
    exit()

# Ввод поискового запроса
search_input_xpath = '//input[@type="text"]'
try:
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, search_input_xpath)))
    logging.info("Поле поиска найдено.")
except Exception as e:
    logging.error(f"Ошибка при ожидании поля поиска: {e}")
    browser.quit()
    exit()

try:
    search_input = browser.find_element(By.XPATH, search_input_xpath)
    search_input.clear()
    search_input.send_keys(search_query)
    search_input.send_keys(Keys.RETURN)
    logging.info(f"Запрос '{search_query}' успешно отправлен.")
    time.sleep(4)
except Exception as e:
    logging.error(f"Ошибка при вводе запроса: {e}")
    browser.quit()
    exit()

# Инициализация данных
results = []
seen_entries = set()
max_results = 100  # Лимит на количество результатов

# Функция для прокрутки страницы до элемента
def scroll_to_element(element):
    """Прокручивает страницу до указанного элемента."""
    browser.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(1)  # Ждем 1 секунду после прокрутки

# Функция для обработки одной карточки
def process_card(business):
    """Обрабатывает одну карточку и извлекает нужные данные."""
    try:
        title = business.find_element(By.CLASS_NAME, 'search-business-snippet-view__title').text
        address = business.find_element(By.CLASS_NAME, 'search-business-snippet-view__address').text
        entry_signature = (title, address)

        if entry_signature in seen_entries:
            return None  # Если карточка уже обработана, возвращаем None

        seen_entries.add(entry_signature)

        phone_numbers = []
        vk_link = "Нет VK"
        website_url = "Нет сайта"

        try:
            # Кликаем по карточке для получения дополнительной информации
            title_element = business.find_element(By.CLASS_NAME, 'search-business-snippet-view__title')
            ActionChains(browser).move_to_element(title_element).click().perform()  # Клик по карточке

            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'card-title-view__title')))

            # Собираем телефоны
            phone_elements = browser.find_elements(By.CLASS_NAME, 'card-phones-view__phone-number')
            for phone in phone_elements:
                clean_phone = phone.text.split('\n')[0]
                phone_numbers.append(clean_phone)

            # Ссылка на сайт
            try:
                website_element = browser.find_element(By.CLASS_NAME, 'business-urls-view__link')
                website_url = website_element.get_attribute('href')
            except:
                pass

            # Ссылка на VK
            try:
                vk_element = browser.find_element(By.XPATH, '//a[contains(@href, "vk.com")]')
                vk_link = vk_element.get_attribute('href')
            except:
                pass

        except Exception as e:
            logging.warning(f"Ошибка при обработке карточки {title}: {e}")

        # Возвращаем собранные данные
        return {'Название': title, 'Адрес': address, 'Телефон': phone_numbers, 'Сайт': website_url, 'VK': vk_link}

    except Exception as e:
        logging.error(f"Ошибка при извлечении данных из карточки: {e}")
        return None

# Главная логика
while len(results) < max_results:
    try:
        # Собираем все карточки на текущей странице
        business_elements = browser.find_elements(By.CLASS_NAME, 'search-business-snippet-view')

        if not business_elements:
            logging.info("Не найдено новых карточек. Последняя карточка достигнута.")
            break

        for business in business_elements:
            card_data = process_card(business)
            if card_data:
                results.append(card_data)

        # Прокрутка страницы
        scroll_to_element(business_elements[-1])

        # Даем время для загрузки новых карточек после прокрутки
        time.sleep(2)

        # Проверка появления новых карточек
        new_business_elements = browser.find_elements(By.CLASS_NAME, 'search-business-snippet-view')
        if len(new_business_elements) == len(business_elements):
            logging.info("Нет новых карточек после прокрутки. Остановка.")
            break

    except Exception as e:
        logging.error(f"Ошибка при обработке списка: {e}")
        break

# Сохранение данных
try:
    unique_results = []
    seen = set()
    for result in results:
        phone_tuple = tuple(result['Телефон'])
        entry_signature = (result['Название'], result['Адрес'], phone_tuple, result['Сайт'], result['VK'])

        if entry_signature not in seen:
            seen.add(entry_signature)
            unique_results.append(result)

    # Сохранение в текстовый файл
    with open("search_results.txt", "w", encoding="utf-8") as txt_file:
        for result in unique_results:
            txt_file.write(f"Название: {result['Название']}\nАдрес: {result['Адрес']}\nТелефон: {', '.join(result['Телефон'])}\nСайт: {result['Сайт']}\nVK: {result['VK']}\n{'-'*40}\n")

    # Сохранение в CSV файл
    df = pd.DataFrame(unique_results)
    df.to_csv('search_results.csv', index=False, encoding='utf-8')
    logging.info("Данные успешно сохранены.")
except Exception as e:
    logging.error(f"Ошибка при сохранении данных: {e}")

browser.quit()
