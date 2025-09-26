import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pyspark.sql import SparkSession

st.text('SQL запросы')

# Настройка Spark сессии
spark = (
    SparkSession.builder.appName("Streamlit SQL App")
    .config("spark.driver.extraClassPath", "/path/to/your/jdbc_driver.jar") # Укажите путь к вашему jdbc-драйверу!
    .getOrCreate()
)

# Подключение к базе данных через JDBC
def connect_to_db(jdbc_url, properties):
    try:
        df = spark.read.jdbc(url=jdbc_url, table="public.your_table", properties=properties)
        return df.toPandas()  # Преобразуем Spark Dataframe в Pandas Dataframe
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None

# Основная логика приложения
def main():
    st.title("Приложение для выполнения SQL-запросов")
    
    db_type = st.selectbox("Выберите тип базы данных", ["PostgreSQL", "MySQL"])
    if db_type == "PostgreSQL":
        driver_class = "org.postgresql.Driver"
        jdbc_url_template = "jdbc:postgresql://{}:{}/{}"
    elif db_type == "MySQL":
        driver_class = "com.mysql.cj.jdbc.Driver"
        jdbc_url_template = "jdbc:mysql://{}:{}/{}"
        
    hostname = st.text_input("Хост:")
    port = st.number_input("Порт:", value=5432 if db_type == "PostgreSQL" else 3306)
    database = st.text_input("Имя базы данных:")
    username = st.text_input("Пользователь:")
    password = st.text_input("Пароль:", type="password")
    
    sql_query = st.text_area("Введите SQL-запрос:", height=150)
    
    if st.button("Выполнить запрос"):
        jdbc_url = jdbc_url_template.format(hostname, port, database)
        properties = {
            "driver": driver_class,
            "user": username,
            "password": password
        }
        
        df = connect_to_db(jdbc_url, properties)
        if df is not None:
            st.dataframe(df.query(sql_query))
            
if __name__ == "__main__":
    main()
