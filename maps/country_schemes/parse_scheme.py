import xml.etree.ElementTree as ET
import re
from collections import defaultdict

# Укажите имя вашего файла без расширения .drawio
NAME = "ecumene"

def process_country_cell(value_text):
    """
    Разделяет содержимое ячейки на имя и блок с годами по границе тегов (<div> или <br>).
    Корректирует все положительные годы на -1 (и в названии, и в периоде).
    Отрицательные годы (со знаком минус или в скобках с минусом) не изменяются.
    """
    if not value_text:
        return "", []

    # Шаг 1. Находим границу между названием и годами через теги
    split_match = re.search(r'(<div\s*>|<br\s*/?>)', value_text)
    
    if split_match:
        idx = split_match.start()
        raw_name = value_text[:idx]
        raw_years = value_text[idx:]
    else:
        # Если тегов нет, ищем блок с отрицательным годом в скобках или дефис-разделитель
        split_match = re.search(r'(-\d+|\(\s*-\d+)', value_text)
        if split_match:
            idx = split_match.start()
            raw_name = value_text[:idx]
            raw_years = value_text[idx:]
        else:
            raw_name = value_text
            raw_years = ""

    # Очищаем название от HTML-тегов
    raw_name = re.sub(r'<[^>]+>', '', raw_name).strip()
    
    # Функция для уменьшения положительных годов на 1
    def decrement_positive_years(match):
        full_match = match.group(0)
        # Если перед числом внутри найденной группы есть минус, это отрицательный год. Не трогаем его.
        if '-' in full_match:
            return full_match
        
        # Извлекаем само число из первой группы захвата
        if match.group(1) is None:
            return full_match
        val = int(match.group(1))
        return str(val - 1) if val > 0 else str(val)

    # Корректируем положительные годы В НАЗВАНИИ страны.
    # Регулярное выражение ищет:
    # Либо отрицательные конструкции вида -1200 или (-1200), чтобы захватить их целиком и пропустить
    # Либо просто группы цифр (\d+), после которых НЕ идет буква 'm'
    pattern = r'\(-\s*\d+\)|\-\s*\d+|(\d++)(?!m)'
    corrected_name = re.sub(pattern, decrement_positive_years, raw_name)

    # Шаг 2. Очищаем блок годов от HTML-тегов
    clean_years_str = re.sub(r'<[^>]+>', ' ', raw_years).strip()
    
    # Шаг 3. Убираем дефисы-разделители диапазона между положительными числами
    clean_years_str = re.sub(r'(?<=\d)-(?=\d)', ' ', clean_years_str)
    
    # Безопасно извлекаем числа.
    # Отрицательные числа извлекаются, только если они были обернуты в скобки: (-1200)
    years_raw = re.findall(r'\(\s*(-?\d+)\s*\)|\b(\d+)\b', clean_years_str)
    
    corrected_years = []
    for match in years_raw:
        y_str = match[0] if match[0] else match[1]
        if not y_str:
            continue
            
        y = int(y_str)
        if y > 0:
            corrected_years.append(y - 1)
        else:
            corrected_years.append(y)

    return corrected_name, corrected_years

def main():
    input_file = f"{NAME}.drawio"
    countries_file = f"{NAME}_countries.txt"
    transforms_file = f"{NAME}_transforms.txt"
    
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except ET.ParseError:
        print(f"Ошибка: Не удалось распарсить {input_file}. Убедитесь, что файл сохранен БЕЗ сжатия.")
        return
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден.")
        return

    countries = {}
    edges = []
    
    source_counts = defaultdict(int)
    target_counts = defaultdict(int)

    # Первый проход: собираем все страны
    for cell in root.iter('mxCell'):
        cell_id = cell.get('id')
        is_vertex = cell.get('vertex') == '1'
        is_edge = cell.get('edge') == '1'
        
        if is_vertex and cell.get('value'):
            value = cell.get('value')
            name, years = process_country_cell(value)
            if name:
                countries[cell_id] = name
                years_str = " ".join(map(str, years))
                countries[cell_id + "_line"] = f"{name} {years_str}".strip()
                countries[cell_id + "_first_year"] = str(years[0]) if years else ""

        elif is_edge:
            source = cell.get('source')
            target = cell.get('target')
            if source and target:
                edges.append({'source': source, 'target': target})
                source_counts[source] += 1
                target_counts[target] += 1

    # Запись в NAME_countries.txt
    with open(countries_file, 'w', encoding='utf-8') as f:
        for cell_id in list(countries.keys()):
            if not cell_id.endswith('_line') and not cell_id.endswith('_first_year'):
                f.write(countries[cell_id + "_line"] + '\n')

    # Второй проход: определяем типы связей и записываем в NAME_transforms.txt
    with open(transforms_file, 'w', encoding='utf-8') as f:
        for edge in edges:
            src_id = edge['source']
            tgt_id = edge['target']
            
            src_name = countries.get(src_id)
            tgt_name = countries.get(tgt_id)
            
            if not src_name or not tgt_name:
                continue
            
            if source_counts[src_id] > 1 and target_counts[tgt_id] > 1:
                edge_type = "SPLITMERGE"    
            elif source_counts[src_id] > 1:
                edge_type = "SPLIT"
            elif target_counts[tgt_id] > 1:
                edge_type = "MERGE"
            else:
                edge_type = "___"
                
            year_val = countries.get(tgt_id + "_first_year", "")

            f.write(f"{src_name} {tgt_name} {edge_type} {year_val}".strip() + '\n')

    print(f"Парсинг успешно завершен!")
    print(f"Созданы файлы: {countries_file} и {transforms_file}")

if __name__ == "__main__":
    main()
