import streamlit as st

import os
from pathlib import Path



st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv","mp3"])

def output_files(DIR_PATH):
    if os.path.exists(DIR_PATH):
        files = [f for f in os.listdir(DIR_PATH) if os.path.isfile(os.path.join(DIR_PATH, f))]
        if len(files) > 0:
            st.subheader("Доступные файлы для скачивания:")
            for file in files:
                st.markdown(download_file(os.path.join(DIR_PATH, file)), unsafe_allow_html=True)
        else:
            st.info("Нет доступных файлов для скачивания.")
    else:
        st.warning("папка не найдена.")    
