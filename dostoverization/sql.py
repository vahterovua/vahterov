import streamlit as st
import pandas as pd
from sqlalchemy import create_engine


st.text('SQL запросы')

# Создание подключения к базе данных PostgreSQL
def create_connection():
    try:
        # Замените значения ниже на ваши реальные данные для подключения
        engine = create_engine('postgresql://your_username:your_password@your_host/your_database_name')
        return engine
    except Exception as e:
        print(f"Ошибка соединения с базой данных: {e}")
        return None

# Выполнение SQL-запросов и сохранение результата в датафрейме
def run_query(query):
    engine = create_connection()
    if engine is not None:
        try:
            df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None
    else:
        return None

# Основной сценарий программы
if __name__ == "__main__":
    sql_input = input("Введите ваш SQL-запрос:\n")  # Для интерактивного ввода в консоли
    
    result_df = run_query(sql_input)
    if result_df is not None:
        print(result_df)

