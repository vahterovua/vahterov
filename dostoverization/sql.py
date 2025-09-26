import streamlit as st
import pandas as pd
from sqlalchemy import create_engine


st.title("SQL-запросы к БД PostgreSQL")

# Функции для обработки взаимодействия с БД
def create_connection(host, port, db_name, username, password):
    """Создаёт соединение с базой данных PostgreSQL."""
    try:
        connection_string = f'postgresql://{username}:{password}@{host}:{port}/{db_name}'
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Ошибка соединения с базой данных: {e}")
        return None


def run_query(engine, query):
    """Выполняет SQL-запрос и возвращает результат в виде DataFrame."""
    if engine is not None:
        try:
            df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            st.error(f"Ошибка выполнения запроса: {e}")
            return None
    else:
        return None


# Интерфейс Streamlit
st.text("введите данные и нажмите 'Выполнить запрос'")

# Форма для ввода данных подключения к базе данных
host = st.text_input("Хост (например, localhost)", "")
port = st.text_input("Порт (например, 5432)", "")
db_name = st.text_input("Название базы данных", "")
username = st.text_input("Имя пользователя", "")
password = st.text_input("Пароль", type="password")

# Поле для ввода SQL-запроса
sql_input = st.text_area("Введите ваш SQL-запрос:", height=150)

# Кнопка для отправки запроса
if st.button("Выполнить запрос"):
    # Проверка заполненных полей
    if all([host, port, db_name, username, password]):
        # Создание подключения к базе данных
        engine = create_connection(host, port, db_name, username, password)
    
        # Выполнение запроса и получение результата
        result_df = run_query(engine, sql_input)
    
        if result_df is not None:
            st.subheader("Результат выполнения запроса:")
            st.dataframe(result_df)
        else:
            st.error("Нет результата.")
    else:
        st.warning("Заполните все обязательные поля!")



result_df.to_excel('результат запроса.xlsx')


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
