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


# Генерируем файл excel и предлагаем скачать
excel_file = result_df.to_excel('data.xlsx')
def download_file(file_path):
    with open(file_path, 'rb') as f:
        file_data = f.read()
    return file_data

# Получаем список всех файлов в текущей директории
files_in_current_dir = [f for f in os.listdir('.') if os.path.isfile(f)]

st.title('Загрузка файлов')
selected_file = st.selectbox("Выберите файл:", files_in_current_dir)

if selected_file is not None:
    # Создаем ссылку на загрузку файла
    data = download_file(selected_file)
    btn = st.download_button(
        label=f"Скачать {selected_file}",
        data=data,
        file_name=selected_file,
        mime="application/octet-stream",
    )
