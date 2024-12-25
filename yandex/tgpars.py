 #id-22998349
#hash-aa16e0f5e484af5a2128274c93122e78
#79225594237
# client = TelegramClient('my_session', api_id, api_hash, system_version='4.16.30-vxCUSTOM')

import pandas as pd
import re
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# Введите свои данные API
api_id = '22998349'  
api_hash = 'aa16e0f5e484af5a2128274c93122e78'

# Ваш номер телефона
phone_number = '+79225594237'

# Путь к Excel-файлу
excel_path = 'output (1).xlsx'  # Входной Excel
output_excel_path = 'exported_usernames.xlsx'  # Выходной Excel

def clean_phone_number(phone):
    # Удаляем все символы, кроме цифр и знака "+"
    return re.sub(r'[^\d+]', '', phone)

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
    # Чтение Excel файла
    df = pd.read_excel(excel_path)

    # Проверяем, что файл содержит правильные данные
    if 'Телефон' not in df.columns:
        print("В файле отсутствует колонка 'Телефон'.")
        return

    # Очищаем данные от пустых строк
    df = df.dropna(subset=['Телефон'])

    contacts_to_add = []
    user_data = []

    # Создание списка контактов из Excel
    for index, row in df.iterrows():
        phone = clean_phone_number(str(row['Телефон']))
        first_name = row['Название']
        last_name = row.get('Город', '')

        # Проверка на корректность номера телефона
        if phone.startswith('+') and len(phone) > 10:
            contact = InputPhoneContact(client_id=index, phone=phone, first_name=first_name, last_name=last_name)
            contacts_to_add.append(contact)
        else:
            print(f"Некорректный номер телефона: {phone}")

    async with TelegramClient('my_session', api_id, api_hash, system_version='4.16.30-vxCUSTOM') as client:
        await client.start(phone_number)

        if contacts_to_add:
            result = await client(ImportContactsRequest(contacts_to_add))
            print(f"Добавлено контактов: {len(result.users)}")
            for user in result.users:
                username = user.username or "Нет username"
                print(f"Имя: {user.first_name}, Username: {username}")
                user_data.append({
                    "Телефон": user.phone,
                    "Имя": user.first_name,
                    "Фамилия": user.last_name or "",
                    "Username": username
                })

            # Сохранение информации о пользователях в Excel
            export_df = pd.DataFrame(user_data)
            export_df.to_excel(output_excel_path, index=False)
            print(f"Данные успешно сохранены в {output_excel_path}")

            # Рассылка сообщений
            print("Начинаем рассылку сообщений...")
            await send_messages(client, user_data)
        else:
            print("Нет контактов для добавления.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
