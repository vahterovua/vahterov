import streamlit as st
import os
from pathlib import Path


def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.
    """
    import base64
    b64 = base64.b64encode(object_to_download.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv","mp3"])

if uploaded_file is not None:
    # Отображаем метаданные файла
    file_details = {"Имя": uploaded_file.name, "Тип": uploaded_file.type, "Размер": uploaded_file.size}
    st.write(file_details)
    
    # Создаем ссылку для скачивания загруженного файла
    st.markdown(download_link(uploaded_file.getvalue().decode(), uploaded_file.name, 'Нажмите сюда, чтобы скачать файл'), unsafe_allow_html=True)
