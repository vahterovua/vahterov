import streamlit as st

# st.components.v1.html(
# """ <iframe frameborder="5" src="https://datalens.yandex/ctuxlru5a0jky?_no_controls=5"></iframe>"""
# )

st.text('инструкция')


import streamlit as st
from github import Github
import os

# Настройки аутентификации GitHub
TOKEN = 'YOUR_GITHUB_TOKEN'
REPO_NAME = 'your_username/your_repo_name' # Укажите ваш username/repo-name

def upload_file_to_github(file_path):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        with open(file_path, 'rb') as file_data:
            content = file_data.read()
            
        # Загружаем файл в корень репозитория
        repo.create_file(os.path.basename(file_path), f"Upload {os.path.basename(file_path)} via Streamlit", content)
    
        return True
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return False


st.title("Загрузка файлов в GitHub")
uploaded_file = st.file_uploader("Выберите файл для загрузки:", type=["txt", "py", "md"])

if uploaded_file is not None:
    if st.button('Отправить файл'):
        temp_dir = '/tmp/'
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        result = upload_file_to_github(file_path)
        
        if result:
            st.success(f"Успешно отправлено: `{file_path}`!")
        else:
            st.error("Что-то пошло не так при отправке файла.")

        # Удаляем временный файл
        os.remove(file_path)

