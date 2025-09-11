import streamlit as st

import os
from pathlib import Path



st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv","mp3"])

uploaded_file
