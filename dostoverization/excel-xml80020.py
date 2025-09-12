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
