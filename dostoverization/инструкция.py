import streamlit as st

# st.components.v1.html(
# """ <iframe frameborder="5" src="https://datalens.yandex/ctuxlru5a0jky?_no_controls=5"></iframe>"""
# )

st.text('инструкция')


import os
from pathlib import Path
import streamlit as st
from github import Github

# Получаем токен OAuth и название репозитория из переменных окружения
token = os.getenv("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")
repo_name = 'vahterovua'
folder_path = 'load'  # Папка внутри репозитория, куда будем заливать файл

def upload_file_to_github(file):
    g = Github(token)
    
    try:
        repo = g.get_user().get_repo(repo_name)
        
        # Читаем содержимое файла
        file_bytes = file.read()
        
        # Генерируем путь относительно корня репозитория
        file_path_in_repo = f"{folder_path}/{file.name}"
        
        # Проверяем наличие файла и обновляем либо создаём новый
        contents = None
        try:
            contents = repo.get_contents(file_path_in_repo)
        except Exception:
            pass
            
        if contents is not None:
            # Обновляем существующий файл
            sha = contents.sha
            commit_message = f"Обновление файла {file.name}"
            result = repo.update_file(file_path_in_repo, commit_message, file_bytes.decode('utf-8'), sha=sha)
        else:
            # Создаем новый файл
            commit_message = f"Загрузка нового файла {file.name}"
            result = repo.create_file(file_path_in_repo, commit_message, file_bytes.decode('utf-8'))
        
        return True
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return False


st.title("Загрузчик файлов в GitHub 📁")

uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "md", "csv"])
if uploaded_file is not None:
    if st.button("Загрузить файл"):
        success = upload_file_to_github(uploaded_file)
        if success:
            st.success(f"Успешно загружено: **{uploaded_file.name}**!")
        else:
            st.error("Что-то пошло не так.")


