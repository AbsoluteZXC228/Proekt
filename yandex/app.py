from flask import Flask, render_template, request
import subprocess
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

REQUEST_FILE = "request.txt"  # Файл для хранения запроса

@app.route("/")
def index():
    """Отображение главной страницы."""
    return render_template("index.html")

@app.route("/run_parser", methods=["POST"])
def run_parser():
    """Запуск парсера с указанным запросом."""
    query = request.form.get("query", "").strip()
    if not query:
        return "Ошибка: запрос не должен быть пустым.", 400

    # Создание и запись запроса в файл
    try:
        with open(REQUEST_FILE, "w", encoding="utf-8") as file:
            file.write(query)
        logging.info(f"Запрос '{query}' сохранён в файл {REQUEST_FILE}.")
    except Exception as e:
        logging.error(f"Ошибка при записи в файл {REQUEST_FILE}: {e}")
        return f"Ошибка при записи запроса: {e}", 500

    # Запуск yandex_parser.py
    try:
        result = subprocess.run(
            ["python", "yandex_parser.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info("Скрипт yandex_parser.py успешно выполнен.")

            # Запуск numparser.py
            numparser_result = subprocess.run(
                ["python", "numparser.py"],
                capture_output=True,
                text=True
            )
            if numparser_result.returncode == 0:
                logging.info("Скрипт numparser.py успешно выполнен.")
                # Очистка файла после выполнения
                os.remove(REQUEST_FILE)
                return "Оба скрипта успешно выполнены! Проверьте файлы результатов."
            else:
                logging.error(f"Ошибка выполнения numparser.py: {numparser_result.stderr}")
                return f"Ошибка выполнения numparser.py: {numparser_result.stderr}", 500
        else:
            logging.error(f"Ошибка выполнения yandex_parser.py: {result.stderr}")
            return f"Ошибка выполнения yandex_parser.py: {result.stderr}", 500
    except Exception as e:
        logging.error(f"Ошибка при запуске скриптов: {e}")
        return f"Ошибка при запуске скриптов: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
