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









import os
import pandas as pd
from lxml import etree

# распаковка zip файла в указанной папке
import zipfile


# Проходимся по всем файлам в папке
for filename in os.listdir(folder_path):
    if filename.endswith('.zip'):  # Проверка, является ли файл ZIP-архивом
        archive_path = os.path.join(folder_path, filename)
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Распаковка архива в текущую директорию
                zip_ref.extractall(path=folder_path)
            
            print(f'Архив {filename} успешно распакован.')
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
#final_df


# Сохранение объединенного датафрейма в CSV-файл
final_df.to_excel(f'{a}\суммаAll.xlsx', index=False)

# Задать Кр
k = 1
# Подсчет количества и суммы значений
count_values = len(final_df['value'])
sum_values = final_df['value'].sum()
print(f"Количество значений: {count_values}")
print(f"Сумма значений без без учета Кр: {sum_values:.4f}")
print(f"Сумма значений с учетом Кр: {k*sum_values:.4f}")

# st.markdown(f'Количество значений: {count_values}')
# st.markdown(f'Сумма значений: {sum_values:.4f}')
# Удаляем исходные файлы после добавления их в архив
for file in os.listdir(folder_path):
    if file.endswith('.xml'):
        full_path = os.path.join(folder_path, file)
        os.remove(full_path)
        print(f'Файл {file} удален')

import plotly.express as px
# Преобразование данных с помощью pivot()
df_pivot = final_df.pivot(index='Дата_время', columns='measuring_point_code', values='value')
# st.markdown(f'Количество точек учета: {len(df_pivot.columns)}')
st.markdown(f'статистика')
st.write(df_pivot.describe().T)
graf=df_pivot.describe().T

st.markdown(f'суммы')
st.write(df_pivot.sum(axis=0))
st.markdown(f'общая таблица')
df_pivot

fig1 = px.bar(df_pivot,x=df_pivot.index,y=df_pivot.columns, title='столбчатые диаграммы потребления электроэнергии в кВт*ч')
# Добавляем подписи данных над каждым столбцом
fig1.update_traces(texttemplate='%{y}', textposition='outside')
fig1

fig = px.line(df_pivot,x=df_pivot.index,y=df_pivot.columns, title='линейные графики потребления электроэнергии в кВт*ч')
# Добавляем подписи данных над каждым столбцом
#fig.update_traces(texttemplate='%{y}', textposition='outside')
fig

# df_pivot.to_excel(F'{a}\сумма.xlsx')
st.markdown(f'конвертация завершена')



# Директория для загрузки файлов
UPLOAD_DIR = f"{a}"
# st.markdown(f'выбрана папка {UPLOAD_DIR}')
df_pivot.to_excel(F'{UPLOAD_DIR}\сумма.xlsx')

# Функция для создания ссылки на скачивание файла
def download_file(filename):
    with open(filename, "rb") as f:
        bytes_data = f.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:file/{filename};base64,{b64}" download="{filename}">{filename}</a>'
    return href

# Кнопка для удаления папки
if st.button("Удалить папку"):
    if os.path.exists(UPLOAD_DIR):
        try:
            shutil.rmtree(UPLOAD_DIR)
            st.success(f"Папка '{UPLOAD_DIR}' удалена.")
        except Exception as e:
            st.error(f"Ошибка при удалении папки: {str(e)}")
    else:
        st.warning(f"Папка '{UPLOAD_DIR}' не найдена.")

# # Отображение файлов для скачивания
# if os.path.exists(UPLOAD_DIR):
#     files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
#     if len(files) > 0:
#         st.subheader("Доступные файлы для скачивания:")
#         for file in files:
#             st.markdown(download_file(os.path.join(UPLOAD_DIR, file)), unsafe_allow_html=True)
#     else:
#         st.info("Нет доступных файлов для скачивания.")
# else:
#     st.warning("Директория для загрузки файлов не найдена.")

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



