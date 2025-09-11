import streamlit as st
import os
from pathlib import Path
st.title("Загрузчик файлов 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:")


# Получаем путь текущего каталога
current_dir = os.getcwd()
files_in_directory = sorted([f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))])

st.title('Файлы в директории')

for file_name in files_in_directory:
    # Полный путь к файлу
    full_path = os.path.join(current_dir, file_name)
    
    col1, col2 = st.columns([8, 2])  # Разделяем экран на две части: ссылка и кнопка
    
    with col1:
        # Создаем ссылку для скачивания
        href = f'<a download="{file_name}" href="data:text/plain;charset=utf-8,{open(full_path).read()}">📥 Скачать "{file_name}"</a>'
        st.markdown(href, unsafe_allow_html=True)
        
    with col2:
        # Кнопка для удаления файла
        if st.button("❌ Удалить", key=file_name):
            success = delete_file(full_path)
            if success:
                st.success(f'Файл "{file_name}" успешно удалён.')
                break  # Обновляем страницу после удаления
