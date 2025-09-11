import streamlit as st

import os
from pathlib import Path



st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv","mp3"])
if uploaded_file is not None:
    if st.button("Загрузить файл"):
        success = upload_file_to_github(uploaded_file)
        if success:
            st.success(f"Успешно загружено: **{uploaded_file.name}**!")
        else:
            st.error("Что-то пошло не так.")


