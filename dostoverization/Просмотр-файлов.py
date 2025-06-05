import streamlit as st
import os
import base64
from PIL import Image
import shutil
from pathlib import Path

st.text(f'файл import_d содержит только скорректированные значения, d - чувствительность')
st.text(f'файл Получасовки_new - все значения в том числе скорректированные ')
st.text(f'файл Получасовки - все значения в том числе скорректированные')



# Функция для создания ссылки на скачивание файла
def download_file(filename):
    with open(filename, "rb") as f:
        bytes_data = f.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:file/{filename};base64,{b64}" download="{filename}">{filename}</a>'
    return href

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

def del_dir(DIR_PATH):
    if st.button("Удалить папку", key="delete_button"):
        if os.path.exists(DIR_PATH):
            try:
                shutil.rmtree(DIR_PATH)
                st.success(f"Папка '{DIR_PATH}' удалена.")
            except Exception as e:
                st.error(f"Ошибка при удалении папки: {str(e)}")
        else:
            st.warning(f"Папка '{DIR_PATH}' не найдена.")



if "dir_name" in st.session_state:
    dir_name = st.session_state.dir_name
    DIR_PATH = f"data/{dir_name}"
    output_files(DIR_PATH)
    del_dir(DIR_PATH)


