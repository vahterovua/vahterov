import streamlit as st
import os
from pathlib import Path
st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:")



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
