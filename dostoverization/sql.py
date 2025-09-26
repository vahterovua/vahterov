import streamlit as st
import pandas as pd
from sqlalchemy import create_engine


st.text('SQL запросы')

# Функция для создания подключения к базе данных PostgreSQL
def create_connection(host, db_name, username, password):
    try:
        connection_string = f'postgresql://{username}:{password}@{host}/{db_name}'
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Ошибка соединения с базой данных: {e}")
        return None

# Выполнение SQL-запросов и отображение результатов
def run_query(engine, query):
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
st.title("Приложение для выполнения SQL-запросов к PostgreSQL")

# Поля ввода данных для подключения к базе данных
host = st.text_input("Хост (например, localhost)", "")
db_name = st.text_input("Название базы данных", "")
username = st.text_input("Имя пользователя", "")
password = st.text_input("Пароль", type="password")

# Поле для ввода SQL-запроса
sql_input = st.text_area("Введите ваш SQL-запрос:")

# Кнопка запуска запроса
if st.button("Выполнить запрос"):
    # Проверяем наличие всех необходимых данных
    if host and db_name and username and password and sql_input.strip():
        # Создаем подключение к базе данных
        engine = create_connection(host, db_name, username, password)
        
        # Выполняем запрос и выводим результат
        result_df = run_query(engine, sql_input)
        if result_df is not None:
            st.dataframe(result_df)
    else:
        st.warning("Заполните все поля!")

