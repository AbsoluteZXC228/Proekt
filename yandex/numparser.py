import os
import re

def filter_lines_with_plus7(input_filename, output_filename):
    # Проверка существования файла для записи
    if not os.path.exists(output_filename):
        # Создание файла, если он не существует
        open(output_filename, 'w').close()
    
    with open(input_filename, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
    
    # Фильтрация строк, содержащих '+7'
    filtered_lines = []
    for line in lines:
        if '+7' in line:
            # Извлечение только номера телефона
            phone_number = re.sub(r'[^0-9]', '', line.split(': ')[1])
            formatted_phone = '+7' + phone_number
            filtered_lines.append(f"{formatted_phone}\n")
    
    # Сохранение фильтрованных строк в отдельном файле
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.writelines(filtered_lines)

# Пример использования
input_filename = 'search_results.txt'
output_filename = 'filtered_output.txt'
filter_lines_with_plus7(input_filename, output_filename)
