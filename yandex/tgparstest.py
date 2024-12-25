import re
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
import os
import csv

# Введите свои данные API
api_id = '22998349'  
api_hash = 'aa16e0f5e484af5a2128274c93122e78'

# Ваш номер телефона
phone_number = '+79225594237'

# Пути к файлам
input_file_path = 'filtered_output.txt'  # Входной текстовый файл с номерами
output_file_path = 'exported_usernames.txt'  # Выходной текстовый файл

def is_valid_phone(phone):
    return phone.startswith('+') and len(phone) > 10

async def send_messages(client, user_data):
    # Получаем текст сообщения от пользователя
    message_text = input("Введите сообщение для отправки: ")
    
    for user in user_data:
        username = user["Username"]
        if username != "Нет username":
            try:
                await client.send_message(username, message_text)
                print(f"Сообщение отправлено пользователю {username}")
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {username}: {e}")
        else:
            print("Пропуск пользователя без username")

async def main():
    # Чтение номеров телефонов из файла
    if not os.path.exists(input_file_path):
        print(f"Файл {input_file_path} не существует.")
        return
    
    with open(input_file_path, 'r') as f:
        phone_numbers = [line.strip() for line in f.readlines()]

    contacts_to_add = []
    user_data = []

    # Создание списка контактов
    for index, phone in enumerate(phone_numbers):
        if is_valid_phone(phone):
            contact = InputPhoneContact(client_id=index, phone=phone)
            contacts_to_add.append(contact)
        else:
            print(f"Некорректный номер телефона: {phone}")

    async with TelegramClient('my_session', api_id, api_hash) as client:
        await client.start(phone_number)

        if contacts_to_add:
            result = await client(ImportContactsRequest(contacts_to_add))
            print(f"Добавлено контактов: {len(result.users)}")
            with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Телефон", "Имя", "Фамилия", "Username"])  # Заголовки
                for user in result.users:
                    username = user.username or "Нет username"
                    print(f"Имя: {user.first_name}, Username: {username}")
                    user_data.append({
                        "Телефон": user.phone,
                        "Имя": user.first_name,
                        "Фамилия": user.last_name or "",
                        "Username": username
                    })
                    writer.writerow([user.phone, user.first_name, user.last_name or "", username])

            print(f"Данные успешно сохранены в {output_file_path}")

            # Рассылка сообщений
            print("Начинаем рассылку сообщений...")
            await send_messages(client, user_data)
        else:
            print("Нет контактов для добавления.")

    # Удаление файла после завершения работы
    os.remove(input_file_path)
    print(f"Файл {input_file_path} удален.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
