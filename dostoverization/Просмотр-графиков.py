import streamlit as st
import os
import plotly.express as px
import locale
import pandas as pd
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from IPython.display import HTML
import openpyxl

if "button_click" not in st.session_state:
    st.session_state.button_click = False

st.title("графики было-стало")
st.markdown("""------""")

if "dir_name" in st.session_state:
    dir_name = st.session_state.dir_name
    folder_path = f'data/{dir_name}'

    option = st.selectbox("", ["график было--стало по идентификатору ТУ", "все графики"])

    if st.button("Обработать", key="test2"):
        st.session_state.button_click = False
        st.session_state.button_click = True

    if st.session_state.button_click:
        if option == "все графики":
            df1=pd.read_excel(os.path.join(folder_path,'30мин.xlsx')) # файл до обработки
            df2=pd.read_excel(os.path.join(folder_path,'Получасовки.xlsx')) # файл после обработки
            df3=pd.read_excel(os.path.join(folder_path,'Отчет_о_достоверизации.xlsx')) # файл после обработки

            df1 = df1.astype(str)
            df2 = df2.astype(str)
            df3 = df3.astype(str)

            l=list(df2['Идентификатор ТУ']) # список

            # Создаем список для хранения отдельных фигур
            figures = []

            for idx, i in enumerate(l):
            # Нахождение строк, содержащих заданное значение
                f1 = df1[df1['Идентификатор ТУ'].str.contains(i)]
                f2 = df2[df2['Идентификатор ТУ'].str.contains(i)]
                f3 = df3[df3['Идентификатор ТУ'].str.contains(i)]
        
                ff = pd.concat([f1, f2])
                ff = ff.iloc[:, 4:]
                ff = ff.T
                ff.index = pd.to_datetime(ff.index, format='%d.%m.%Y %H:%M')

                # Преобразуем все столбцы в float
                for col in ff.columns:
                    ff[col] = ff[col].replace('-', np.nan).astype(float)

                # Преобразование индекса в столбец 'дата_время'
                ff.reset_index(inplace=True)
                ff.rename(columns={'index': 'дата_время'}, inplace=True)
                ff.columns = ['дата_время', 'было', 'стало']

                # Создание отдельного графика
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=ff['дата_время'], y=ff['было'], name='было'))
                fig.add_trace(go.Scatter(x=ff['дата_время'], y=ff['стало'], name='стало'))

                # Настройка заголовков и аннотаций
                fig.update_xaxes(title_text="Дата/Время")
                fig.update_yaxes(title_text="Значение")
                fig.update_layout(
                    title={
                        'text': f"{i}, ТУ: {f3.iloc[0,1]}, расхождение: {f3.iloc[0,6]} кВт*ч",
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'yref': 'paper',
                        'xref': 'paper',
                        'x': 0.5,
                        'y': 0.95
                    },
                    template='ggplot2'
                )

                figures.append(fig)
                st.markdown(f"{i}, ТУ: {f3.iloc[0,1]}, расхождение: {f3.iloc[0,6]} кВт*ч")
                fig
        elif option == "график было--стало по идентификатору ТУ":
            st.markdown("""точки учета, по которым была произведена достоверизация""")
            df1=pd.read_excel(os.path.join(folder_path, '30мин.xlsx'), decimal=',',dtype='str') # файл до обработки
            df2=pd.read_excel(os.path.join(folder_path, 'Получасовки.xlsx'), decimal=',',dtype='str') # файл после обработки
            df3=pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx'), decimal=',',dtype='str') # файл после обработки

            df3=df3[['Идентификатор ТУ','ТУ','Расход по разности показаний, кВт*ч','Сумма 30 минутных интервалов, кВт*ч','НБ, кВт*ч','Обьем,% 30 минутных интервалов','Примечание']]
            df3.columns=['Идентификатор ТУ','ТУ','W,кВт*ч','W30мин,кВт*ч','НБ,кВт*ч','М30,%','Примечание']
            df3=df3.query('Примечание=="Требуется достоверизация"')

            df3

            # Поле ввода для переменной id
            id = st.text_input("для построения графика введите значение Идентификатор ТУ и нажмите Enter:", value="")
            # Проверяем наличие введенного значения
            if not id:
                # Если значение не введено, выводим сообщение
                st.error("Значение Идентификатор ТУ не введено.")
            else:
                # Если значение введено, выводим его
                st.success(f"Введено: {id}")

            # Нахождение строк, содержащих заданное значение
            f1 = df1[df1['Идентификатор ТУ'].str.contains(id)]
            f2 = df2[df2['Идентификатор ТУ'].str.contains(id)]
            f3 = df3[df3['Идентификатор ТУ'].str.contains(id)]
            ff = pd.concat([f1, f2])
            ff = ff.iloc[:, 4:]  # Оставляем только нужные столбцы
            ff = ff.T
            ff.index = pd.to_datetime(ff.index, format='%d.%m.%Y %H:%M')


            # Преобразование индекса в столбец 'дата_время'
            ff.reset_index(inplace=True)
            ff.rename(columns={'index': 'дата_время'}, inplace=True)
            ff.columns = ['дата_время', 'было', 'стало']  # Переименовываем столбцы
            # Преобразуем все столбцы в float
            ff['было'] = ff['было'].replace('-', np.nan).astype(float)
            ff['стало'] = ff['стало'].replace('-', np.nan).astype(float)
            # Создаем график
            fig = px.line(ff, x='дата_время', y=['было', 'стало'],title=f'{id}, ТУ: {f3.iloc[0,1]}, расхождение: {f3.iloc[0,4]} кВт*ч')


            # Добавляем метки значений к линиям
            fig.update_traces(textposition='top center')
            fig

            df2 = df2[df2['Идентификатор ТУ'].str.contains(id)]

            # Получаем список столбцов, начиная с 4-го
            columns_to_replace = df2.columns[3:]

            # Применяем замену точки на запятую только к указанным столбцам
            for col in columns_to_replace:
                df2[col] = df2[col].str.replace('.', ',')

            fig.update_layout(template='ggplot2')  # Стиль ggplot2

            fig.write_html(os.path.join(folder_path, f'график-{id}.html'))

            # st.markdown('анализ по одной точке [перейти](http://10.167.2.12:8503/).')

            df2.to_excel(f'{folder_path}/шаблон30мин-{id}.xlsx',index=False)
            st.markdown(f'шаблон30мин-{id} сохранен')