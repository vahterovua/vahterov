# Streamlit run XML80020--Excel.py
import streamlit as st
st.title("конвертер XML80020-Excel")
st.markdown("""создать папку на диске P и скопировать zip архив с макетами XML80020:""")
st.markdown("""нажать кнопку Обновить страницу""")
a = st.text_input("введите имя папки и нажмите enter:", value="")

import os
import pandas as pd
from lxml import etree

# распаковка zip файла в указанной папке
import zipfile
# Указываем путь к папке с архивами
folder_path = F'P:\{a}'

st.markdown(f'после завершения работы конвертера в папке {folder_path} сформируется файл сумма.xlsx')

# Проходимся по всем файлам в папке
for filename in os.listdir(folder_path):
    if filename.endswith('.zip'):  # Проверка, является ли файл ZIP-архивом
        archive_path = os.path.join(folder_path, filename)
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Распаковка архива в текущую директорию
                zip_ref.extractall(path=folder_path)
            
            print(f'Архив {filename} успешно распакован.')
            st.markdown(f'обработан {filename}')
        except Exception as e:
            print(f'Ошибка при распаковке архива {filename}: {e}')


# Функция для парсинга одного XML-файла
def parse_xml_file(file_path):
    tree = etree.parse(file_path)
    
    # Пример извлечения некоторых данных из XML
    timestamp = tree.find('.//timestamp').text
    sender_name = tree.find('.//sender/name').text
    day = tree.find('.//day').text
    measuring_points_data = []
    
    for measuring_point in tree.findall('.//measuringpoint'):
        measuring_point_name = measuring_point.get('name')
        measuring_point_code = measuring_point.get('code')
        periods = []
        
        for period in measuring_point.findall('.//period'):
            start = period.get('start')
            end = period.get('end')
            value = period.find('./value').text
            
            periods.append({
                'timestamp': timestamp,
                'sender_name': sender_name,
                'measuring_point_name': measuring_point_name,
                'measuring_point_code': measuring_point_code,
                'day': day,
                'start': start,
                'end': end,
                'value': value
            })
        
        measuring_points_data.extend(periods)
    
    return measuring_points_data
   
# Чтение всех XML-файлов из папки
dataframes = []

for filename in os.listdir(folder_path):
    if filename.endswith('.xml'):
        file_path = os.path.join(folder_path, filename)
        df = pd.DataFrame(parse_xml_file(file_path))
        dataframes.append(df)

# Объединение всех датафреймов в один
final_df = pd.concat(dataframes, ignore_index=True)

# Преобразование значений в числовой формат
final_df['value'] = final_df['value'].str.replace(',', '.').astype(float)

# Преобразуем дату и время в нужный формат
def format_datetime(row):
    date_str = row['day'] # Получаем строку с датой
    time_str = row['end'] # Получаем строку со временем
    
    # Формируем строку в формате 'YYYY-MM-DD HH:MM'
    datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    datetime_str += f" {time_str[:2]}:{time_str[2:]}"
    
    return pd.to_datetime(datetime_str)

# Применяем функцию к каждому ряду для получения новой колонки
final_df['Дата_время'] = final_df.apply(format_datetime, axis=1)
final_df=final_df[['measuring_point_name','measuring_point_code','value','Дата_время']]
final_df


# Сохранение объединенного датафрейма в CSV-файл
final_df.to_excel(F'P:\{a}\сумма.xlsx', index=False)

# Задать Кр
k = 1
# Подсчет количества и суммы значений
count_values = len(final_df['value'])
sum_values = final_df['value'].sum()
print(f"Количество значений: {count_values}")
print(f"Сумма значений без без учета Кр: {sum_values:.4f}")
print(f"Сумма значений с учетом Кр: {k*sum_values:.4f}")
st.markdown(f'Количество значений: {count_values}')
st.markdown(f'Сумма значений: {sum_values:.4f}')
# Удаляем исходные файлы после добавления их в архив
for file in os.listdir(folder_path):
    if file.endswith('.xml'):
        full_path = os.path.join(folder_path, file)
        os.remove(full_path)
        print(f'Файл {file} удален')

import plotly.express as px


fig = px.bar(final_df,x='Дата_время',y='value', title='график потребления электроэнергии в кВт*ч')

# Добавляем подписи данных над каждым столбцом
fig.update_traces(texttemplate='%{y}', textposition='outside')

fig
st.markdown(f'конвертация завершена, итоговый файл - P:\{a}\сумма.xlsx')