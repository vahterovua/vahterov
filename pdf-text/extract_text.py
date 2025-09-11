import PyMuPDF
import pandas as pd
from io import BytesIO
import streamlit as Streamlit

def extract_text_and_tables_from_pdf(file):
    doc = PyMuPDF.open(stream=file.read(), filetype="pdf")
    text_pages = []
    tables_pages = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Извлекаем текст страницы
        text = page.get_text("text")
        text_pages.append(text)
        
        # Извлекаем таблицу
        table_data = page.extract_table()
        if len(table_data) > 0:
            df = pd.DataFrame(table_data[1:], columns=table_data[0])
            tables_pages.append(df)
            
    return "\n\n".join(text_pages), tables_pages


# Функция для конвертации DataFrame'ов в единый Excel-файл
def convert_to_excel(tables):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    
    for idx, df in enumerate(tables):
        sheet_name = f"Таблица {idx+1}"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    writer.save()
    processed_data = output.getvalue()
    return processed_data


Streamlit.title('Распознавание текста и таблиц из PDF файла')
uploaded_file = Streamlit.file_uploader("Выберите PDF файл:", type=["pdf"])

if uploaded_file is not None:
    with Streamlit.spinner("Обработка..."):
        extracted_text, extracted_tables = extract_text_and_tables_from_pdf(uploaded_file)
    
    Streamlit.subheader("Извлечённый текст:")
    Streamlit.text_area("", value=extracted_text, height=300)
    
    if len(extracted_tables) > 0:
        Streamlit.subheader("Таблицы:")
        for i, df in enumerate(extracted_tables):
            Streamlit.write(f"Таблица {i + 1}:")
            Streamlit.dataframe(df)
        
        excel_bytes = convert_to_excel(extracted_tables)
        Streamlit.download_button(
            label="Скачать результаты в Excel",
            data=excel_bytes,
            file_name="output.xlsx",
            mime="application/vnd.ms-excel"
        )




