import streamlit as st

import os
from pathlib import Path



st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv","mp3"])

if uploaded_file is not None:
    # Отображаем метаданные файла
    file_details = {"Имя": uploaded_file.name, "Тип": uploaded_file.type, "Размер": uploaded_file.size}
    st.write(file_details)
    
    # Создаем ссылку для скачивания загруженного файла
    st.markdown(download_link(uploaded_file.getvalue().decode(), uploaded_file.name, 'Нажмите сюда, чтобы скачать файл'), unsafe_allow_html=True)
