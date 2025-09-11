import streamlit as st
import os
from pathlib import Path
st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:")

# Получаем список файлов в текущей директории
files = os.listdir(".")

for file in files:
    # Создаем ссылку на скачивание файла
    download_link = f"[Download {file}]({os.path.abspath(file)})"
    
    # Добавляем ссылку на скачивание в Streamlit
    st.markdown(download_link)

    # Создаем ссылку на удаление файла
    delete_link = f"<a href='javascript:void(0);' onclick=\"if(confirm('Are you sure you want to delete {file}?')){{window.location.href='/delete_file/{file}'}}\">Delete {file}</a>"
    
    # Добавляем ссылку на удаление в Streamlit
    st.markdown(delete_link, unsafe_allow_html=True)
