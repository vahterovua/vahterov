import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

st.text('SQL запросы')

st.text('введите параметры подключения к БД:')


# Поля ввода для каждого параметра соединения
user = st.text_input("Имя пользователя:")
password = st.text_input("Пароль:", type="password")
host = st.text_input("Хост:")
port = st.number_input("Порт:", min_value=1, max_value=65535)
database = st.text_input("Название базы данных:")

if user and password and host and port and database:
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    try:
        engine = create_engine(connection_string, connect_args={"sslmode": "require"})
        
        # Здесь можно продолжить работу с базой данных
        st.success(f"Успешное подключение к {database}")
    
    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
else:
    st.warning("Заполните все необходимые поля.")


# Заголовок страницы
st.title("SQL запрос")

# Поле ввода многострочного текста
request = st.text_area(label="Введите ваш текст:", value="", height=200)

# Кнопка отправки формы
if st.button("Отправить"):
    if input_text.strip():
        # Обработка введённого текста
        st.write(f"обработка запроса:\n\n{input_text}")
    else:
        st.warning("Вы ничего не ввели.")

pd.io.sql.read_sql(request, con = engine)

