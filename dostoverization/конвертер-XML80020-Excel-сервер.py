import streamlit as st
import os
import base64
import shutil
import pandas as pd
from lxml import etree
import zipfile
import plotly.express as px

# Заголовок приложения
st.title("Конвертер XML → Excel")

# Директория для обработки файлов
folder_path = st.text_input("Введите путь к директории:", "")

# Уведомление пользователя
st.markdown(
    f"""
    После завершения работы конвертера в папке `{folder_path}` появится файл `сумма.xlsx`. Перед следующим использованием конвертера удалите все файлы из папки.
    """
)

# Обработчик загрузки файлов
uploaded_files = st.file_uploader("Выберите файлы для загрузки", accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(folder_path, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.success(f"{len(uploaded_files)} файлов успешно загружено в папку '{folder_path}'.")
elif folder_path:
    st.info("Файлы ещё не были выбраны.")

# Распаковка .zip файлов в заданной папке
for filename in os.listdir(folder_path):
    if filename.endswith(".zip"):
        try:
            with zipfile.ZipFile(os.path.join(folder_path, filename)) as zf:
                zf.extractall(folder_path)
            st.success(f"Архив {filename} успешно распакован.")
        except Exception as e:
            st.error(f"Ошибка при распаковке архива {filename}: {e}.")

# Парсер XML файлов
def parse_xml_file(file_path):
    tree = etree.parse(file_path)
    rows = []
    timestamp = tree.find(".//timestamp").text
    sender_name = tree.find(".//sender/name").text
    day = tree.find(".//day").text
    
    for point in tree.findall(".//measuringpoint"):
        name = point.get("name")
        code = point.get("code")
        for period in point.findall(".//period"):
            start_time = period.get("start")
            end_time = period.get("end")
            value = float(period.find("./value").text.replace(",", "."))
            rows.append((timestamp, sender_name, name, code, day, start_time, end_time, value))
    
    return rows

# Сбор данных из всех XML файлов
rows = []
for filename in os.listdir(folder_path):
    if filename.endswith(".xml"):
        rows.extend(parse_xml_file(os.path.join(folder_path, filename)))

# Создание DataFrame
columns = ["timestamp", "sender_name", "measuring_point_name", "measuring_point_code", "day", "start", "end", "value"]
final_df = pd.DataFrame(rows, columns=columns)

# Преобразование даты-времени
final_df["Дата_время"] = (
    final_df["day"].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}")
    + " "
    + final_df["end"].apply(lambda x: f"{x[:2]}:{x[2:]}")
)
final_df["Дата_время"] = pd.to_datetime(final_df["Дата_время"])

# Очистка ненужных столбцов
final_df = final_df[["measuring_point_name", "measuring_point_code", "value", "Дата_время"]]

# Сохранение результата в Excel
final_df.to_excel(f"{folder_path}/суммаAll.xlsx", index=False)

# Статистика по данным
k = 1
count_values = len(final_df["value"])
sum_values = final_df["value"].sum()
st.markdown(f"Количество значений: **{count_values}**")
st.markdown(f"Сумма значений (без учёта Kₚ): **{sum_values:.4f}**")
st.markdown(f"Сумма значений (с учётом Kₚ={k}): **{(k * sum_values):.4f}**")

# Удаление XML файлов
for file in os.listdir(folder_path):
    if file.endswith(".xml"):
        os.remove(os.path.join(folder_path, file))
        st.info(f"Файл {file} удалён.")

# График потребления энергии
df_pivot = final_df.pivot(index="Дата_время", columns="measuring_point_code", values="value")
fig1 = px.bar(df_pivot, x=df_pivot.index, y=df_pivot.columns, title="Графики потребления электроэнергии в кВт⋅ч")
fig1.update_traces(texttemplate="%{y}", textposition="outside")
st.plotly_chart(fig1)

# Сохранение сводного графика
df_pivot.to_excel(f"{folder_path}/сумма.xlsx")
st.markdown(f"Конвертация завершена, итоговый файл — `{folder_path}/сумма.xlsx`.")

# Кнопка для очистки директории
if st.button("Удалить папку"):
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            st.success(f"Папка '{folder_path}' удалена.")
        except Exception as e:
            st.error(f"Ошибка при удалении папки: {e}.")
    else:
        st.warning(f"Папка '{folder_path}' не найдена.")
