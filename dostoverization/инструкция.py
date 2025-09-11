import streamlit as st
import os
from pathlib import Path
st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:")

# Получаем список файлов в текущей директории
files = os.listdir(".")

for file in files:
    # Создаем ссылку на скачивание файла
    download_link = f"({os.path.abspath(file)}"
    
    # Добавляем ссылку на скачивание в Streamlit
    st.markdown(download_link)
