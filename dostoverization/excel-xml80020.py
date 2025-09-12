import streamlit as st
import os
import base64
from PIL import Image
import shutil
st.title("конвертер XML80020-Excel")

a = st.text_input("введите имя папки и нажмите enter:", value="")

folder_path=f'{a}'
st.markdown(f'выбрана папка {folder_path}')

if not os.path.exists(folder_path):
    os.makedirs(folder_path)

st.title("загрузить zip архив с макетами xml80020")

uploaded_files = st.file_uploader("Выберите файлы для загрузки", accept_multiple_files=True)

if uploaded_files is not None:
    for file in uploaded_files:
        with open(os.path.join(folder_path, file.name), "wb") as f:
            f.write(file.getbuffer())

    st.success(f"{len(uploaded_files)} файлов успешно загружены в папку '{folder_path}'.")
else:
    st.info("Файлы еще не были выбраны.")


from lxml import etree
import pandas as pd
from datetime import datetime
import os
import zipfile
import plotly.express as px
# import streamlit as st
def create_xml_for_day(day_data, abonent, code, timestamp):
    """Создает XML файл для одного дня"""
    day = day_data.iloc[0, 3]
    day_number = day[-2:]
    
    # Создание корневого элемента message
    root = etree.Element('message')
    root.attrib['class'] = '80020'
    root.attrib['version'] = '2'
    root.attrib['number'] = day_number

    # Добавление datetime
    datetime_element = etree.SubElement(root, 'datetime')
    etree.SubElement(datetime_element, 'timestamp').text = timestamp
    etree.SubElement(datetime_element, 'daylightsavingtime').text = '1'
    etree.SubElement(datetime_element, 'day').text = day

    # Добавление sender
    sender_element = etree.SubElement(root, 'sender')
    etree.SubElement(sender_element, 'inn').text = '1'
    etree.SubElement(sender_element, 'name').text = abonent

    # Добавление area
    area_element = etree.SubElement(root, 'area')
    etree.SubElement(area_element, 'inn').text = '1'
    etree.SubElement(area_element, 'name').text = abonent

    # Добавление measuringpoint
    measuring_point_element = etree.SubElement(area_element, 'measuringpoint')
    measuring_point_element.attrib['code'] = code
    measuring_point_element.attrib['name'] = abonent

    # Добавление measuringchannel
    measuring_channel_element = etree.SubElement(measuring_point_element, 'measuringchannel')
    measuring_channel_element.attrib['code'] = '01'
    measuring_channel_element.attrib['desc'] = abonent

    # Заполнение периодов из DataFrame
    for _, row in day_data.iterrows():
        period_element = etree.SubElement(measuring_channel_element, 'period')
        period_element.attrib['start'] = row['start']
        period_element.attrib['end'] = row['end']
        
        value_element = etree.SubElement(period_element, 'value')
        value_element.text = str(row['value'])
        value_element.attrib['status'] = '1'

    # Преобразование дерева в строку
    xml_string = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='windows-1251')

    # Запись XML в файл
    filename = f'{abonent}-{day}-{code}.xml'
    with open(filename, 'wb') as f:
        f.write(xml_string)
    
    print(f'XML файл {filename} успешно создан!')
    return filename

def parse_xml_file(file_path):
    """Парсит XML файл и возвращает данные в виде списка словарей"""
    tree = etree.parse(file_path)
    
    timestamp = tree.find('.//timestamp').text
    sender_name = tree.find('.//sender/name').text
    day = tree.find('.//day').text
    measuring_points_data = []
    
    for measuring_point in tree.findall('.//measuringpoint'):
        measuring_point_name = measuring_point.get('name')
        measuring_point_code = measuring_point.get('code')
        
        for period in measuring_point.findall('.//period'):
            start = period.get('start')
            end = period.get('end')
            value = period.find('./value').text
            
            measuring_points_data.append({
                'timestamp': timestamp,
                'sender_name': sender_name,
                'measuring_point_name': measuring_point_name,
                'measuring_point_code': measuring_point_code,
                'day': day,
                'start': start,
                'end': end,
                'value': value
            })
    
    return measuring_points_data

def main():
    # folder_path = os.getcwd()
    
    # Чтение данных из Excel
    try:
        df = pd.read_excel('табл_в_XML80020.xlsx', sheet_name='в_макет80020', dtype=str)
    except FileNotFoundError:
        print("Ошибка: Файл 'табл_в_XML80020.xlsx' не найден!")
        return
    # display(df)
    # Извлечение общей информации
    abonent = df.columns[4] if len(df.columns) > 4 else "Unknown"
    month = df.columns[6] if len(df.columns) > 6 else "Unknown"
    code = df.iloc[0, 4] if len(df) > 0 and len(df.columns) > 4 else "Unknown"
    
    # Формирование метки времени
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Разделение данных по дням (по 48 строк на день)
    day_dataframes = []
    for i in range(0, len(df), 48):
        day_df = df.iloc[i:i+48]
        if not day_df.empty:
            day_dataframes.append(day_df)
    
    # Создание XML файлов для каждого дня
    xml_files = []
    for i, day_df in enumerate(day_dataframes, 1):
        try:
            filename = create_xml_for_day(day_df, abonent, code, timestamp)
            xml_files.append(filename)
        except Exception as e:
            print(f"Ошибка при создании XML для дня {i}: {e}")
    
    # Создание ZIP архива
    if xml_files:
        zip_file_name = f'{abonent}_{month}.zip'
        try:
            with zipfile.ZipFile(zip_file_name, 'w') as zip_archive:
                for file in xml_files:
                    zip_archive.write(file, arcname=file)
                    print(f'Файл {file} добавлен в архив')
            
            # Удаление XML файлов после архивации
            for file in xml_files:
                os.remove(file)
                print(f'Файл {file} удален')
                
        except Exception as e:
            print(f"Ошибка при создании архива: {e}")
    
    # Распаковка и анализ данных
    try:
        # Распаковка архива
        if os.path.exists(zip_file_name):
            with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
                zip_ref.extractall(path=folder_path)
            print(f'Архив {zip_file_name} успешно распакован.')
        
        # Чтение и анализ XML файлов
        dataframes = []
        for filename in os.listdir(folder_path):
            if filename.endswith('.xml'):
                file_path = os.path.join(folder_path, filename)
                try:
                    df_data = pd.DataFrame(parse_xml_file(file_path))
                    dataframes.append(df_data)
                except Exception as e:
                    print(f"Ошибка при парсинге файла {filename}: {e}")
        
        if dataframes:
            # Объединение данных
            final_df = pd.concat(dataframes, ignore_index=True)
            # Сохранение в Excel
            final_df.to_excel('сумма_по_всем_xml.xlsx', index=False)
            # Преобразование и анализ значений
            final_df['value'] = final_df['value'].str.replace(',', '.').astype(float)
            count_values = len(final_df)
            sum_values = final_df['value'].sum()
            print(f"\nРезультаты обработки:")
            print(f"Месяц: {month}")
            print(f"Потребитель: {abonent}")
            print(f"Код счетчика: {code}")
            print(f"Количество значений: {count_values}")
            print(f"Сумма значений: {sum_values:.4f}")
            st.write(px.line(pd.read_excel('табл_в_XML80020.xlsx'),x='дата_время',y=['value','день_нед'],title=f'график {abonent} в екселе').show())
            px.line(pd.read_excel('сумма_по_всем_xml.xlsx')[['value']],title=f'график {abonent} в xml80020').show()
            px.line(pd.read_excel('табл_в_XML80020.xlsx'),x='дата_время',y=['value','день_нед'],title=f'график {abonent} в екселе').write_html(f'{abonent}_до.html')
            px.line(pd.read_excel('сумма_по_всем_xml.xlsx')[['value']],title=f'график {abonent} в екселе').write_html(f'{abonent}_после.html')
            # Очистка XML файлов после обработки
            for filename in os.listdir(folder_path):
                if filename.endswith('.xml'):
                    os.remove(os.path.join(folder_path, filename))
                    print(f'Файл {filename} удален')
        else:
            print("Нет данных для анализа")
            
    except Exception as e:
        print(f"Ошибка при анализе данных: {e}")

if __name__ == "__main__":
    main()































def download_file(file_path):
    """Генерирует ссылку для скачивания файла."""
    with open(file_path, mode='rb') as file:
        return file.read()

# Получение списка всех файлов в текущей рабочей директории
current_directory = os.getcwd()  # Текущий рабочий каталог
all_files = [f for f in os.listdir(current_directory) if os.path.isfile(os.path.join(current_directory, f))]

if len(all_files) > 0:
    st.subheader('Доступные файлы для скачивания:')
    for file in all_files:
        file_path = os.path.join(current_directory, file)
        button_label = f"📥 {file}"
        # Создаем кнопку для скачивания каждого файла
        st.download_button(
            label=button_label,
            data=download_file(file_path),
            file_name=file,
            mime=None,  # Auto-detect MIME type based on the extension
            key=file  # Уникальный ключ для каждой кнопки
        )
else:
    st.info("Нет доступных файлов для скачивания.")
