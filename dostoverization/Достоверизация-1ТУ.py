import streamlit as st
import os
import base64
from PIL import Image
import shutil
import numpy as np
import pandas as pd
import os
import sys
import logging
from pandas.api.types import is_string_dtype
import warnings
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openpyxl

if "button_click" not in st.session_state:
    st.session_state.button_click = False

def upload_files():
    uploaded_files = st.file_uploader("Выберите файлы для загрузки", accept_multiple_files=True)
    if uploaded_files is not None:
        for file in uploaded_files:
            with open(os.path.join(folder_path, file.name), "wb") as f:
                f.write(file.getbuffer())

        if len(uploaded_files) > 0:
            st.success(f"{len(uploaded_files)} файлов успешно загружены в папку '{folder_path}'.")
    else:
        st.info("Файлы еще не были выбраны.")

def count_non_numeric(row):
    return row.isna().sum()

def has_long_sequence_of_dashes(date_cols):
    dash_count = 0
    for val in date_cols:
        if pd.isna(val):
            dash_count += 1
            if dash_count > 3:
                return True
        else:
            dash_count = 0
    return False

def prim(row, date_cols):
    nb_kwh = row.get('НБ, кВт*ч', np.nan)
    sum_intervals = row.get('Сумма 30 минутных интервалов, кВт*ч', np.nan)

    if pd.notna(nb_kwh) and pd.notna(sum_intervals) and nb_kwh > 0.5 * sum_intervals:
        return 'Слишком большое отклонение'
    elif has_long_sequence_of_dashes(date_cols):
        return 'Больше трех пропусков'
    elif is_string_dtype(row.iloc[2]) or is_string_dtype(row.iloc[3]) or row.iloc[3] == '-':
        return 'Отсутствует показание на начало или конец периода'
    elif is_string_dtype(row.iloc[4]) or is_string_dtype(row.iloc[5]) or pd.isna(row.iloc[4]) or pd.isna(row.iloc[5]):
        return 'Недостаточно данных'
    elif row['Обьем,% 30 минутных интервалов'] <= 90:
        return 'Недостаточный объем сбора данных'
    elif row['НБ, кВт*ч'] != 0 or (row['НБ, кВт*ч'] == 0 and row['Обьем,% 30 минутных интервалов'] != 100):
        return 'Требуется достоверизация'
    else:
        return 'Достоверно'
    
def color_vol(value):
    return 'background-color: #c6efce' if value['Обьем,% 30 минутных интервалов'] >= 90 else ''

    
def color_prim(value):
    if value == 'Требуется достоверизация': return 'background-color: #ffeb9c'
    elif value == 'Достоверно': return 'background-color: #c6efce'
    else: return ''

def color(row):
    styles = [''] * len(row)

    if row['НБ, кВт*ч'] == 0:
        styles[row.index.get_loc('НБ, кВт*ч')] = 'background-color: #c6efce'

    if row['Обьем,% 30 минутных интервалов'] == 100:
        styles[row.index.get_loc('Обьем,% 30 минутных интервалов')] = 'background-color: #c6efce'
    
    if row['Примечание'] == 'Достоверно':
        styles[row.index.get_loc('Примечание')] = 'background-color: #c6efce'
    elif row['Примечание'] == 'Требуется достоверизация':
        styles[row.index.get_loc('Примечание')] = 'background-color: #ffeb9c'
    
    return styles

def fill_provokes_dynamic(values_row, nb):
    """
    Корректирует данные с учетом провалов, основываясь на динамическом подходе.

    Args:
        values_row (pd.Series): Строка с данными потребления (получасовки).
        nb (float): НБ, кВт*ч, доступный для заполнения провалов.

    Returns:
        tuple: Исправленные данные (pd.Series) и оставшееся значение НБ.
    """
    values = values_row.values
    corrected = values.copy()

    overall_mean = np.mean(values)
    provokes = []

    for i in range(1, len(values) - 1):
        prev_val, curr_val, next_val = values[i - 1], values[i], values[i + 1]

        if (
            i > 1 and
            i + 1 < len(values) and
            values[i - 1] < 0.1 * overall_mean and
            values[i] < 0.1 * overall_mean and
            values[i + 1] < 0.1 * overall_mean
        ):
            continue

        if abs(curr_val - prev_val) / max(prev_val, 1) > 0.5 and abs(curr_val - next_val) / max(next_val, 1) > 0.5:
            avg_val = (prev_val + next_val) / 2
            deviation = abs(curr_val - avg_val)
            provokes.append((i, deviation))

    provokes.sort(key=lambda x: x[1], reverse=True)

    for i, _ in provokes:
        prev_val, curr_val, next_val = values[i - 1], values[i], values[i + 1]
        avg_val = (prev_val + next_val) / 2

        correction = avg_val - curr_val

        if correction <= nb:
            corrected[i] = avg_val
            nb -= correction
        else:
            corrected[i] = curr_val + nb
            nb = 0
            break

    if nb > 0:
        valid_indices = [
            i for i in range(len(values))
            if not (
                i > 1 and
                i + 1 < len(values) and
                values[i - 1] < 0.1 * overall_mean and
                values[i] < 0.1 * overall_mean and
                values[i + 1] < 0.1 * overall_mean
            )
        ]

        if valid_indices:
            nb_per_index = nb / len(valid_indices)
            for i in valid_indices:
                corrected[i] += nb_per_index
                nb -= nb_per_index
    return pd.Series(corrected, index=values_row.index)


st.title("достоверизация 2 варианта по одной точке")

if "dir_name" in st.session_state:
    dir_name = st.session_state.dir_name
    folder_path = f'data/one_pu/{dir_name}'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    st.markdown("""1. выбрать одну точку чета, где есть расхождение""")
    st.markdown("""2. выгрузить отчет из пирамиды "шаблон импорта произвольных данных по параметру ....Энергия А+ за 30 минут """)
    st.markdown("""3. переименовать файл 30 мин.xlsx и загрузить в папку""")
    st.markdown('для точек учета, где имеются провалы более 3-х 30 минуток подряд, может применяться достоверизация по 2-му варианту, для таких точек необходимо в шаблоне 30мин заменить "-" на нули')
    st.title("загрузить файлы")
    upload_files()

    if st.button("Обработать", key="test"):
        st.session_state.button_click = False
        st.session_state.button_click = True


    if st.session_state.button_click:
        file3 = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'), decimal=',')
        date_columns = [col for col in file3.columns if ":" in col and '.' in col]
        file3[date_columns] = file3[date_columns].replace(["-", "", " "], np.nan).apply(pd.to_numeric, errors='coerce')
        sum_30_min_intervals = file3[date_columns].sum(axis=1)
        dataframe = pd.DataFrame({'my_column': sum_30_min_intervals})
        st.markdown(f'загружен файл 30мин.xlsx по точке учета : {file3.iloc[0,1]}')
        st.markdown(f'сумма 30 минуток :{dataframe.iloc[0,0]}')

        volume_percent = (((len(date_columns)) - file3[date_columns].apply(count_non_numeric, axis=1)) / len(date_columns) * 100).round(1)
        df3 = pd.concat([file3[['Идентификатор ТУ']],sum_30_min_intervals.rename('Сумма 30 минутных интервалов, кВт*ч'),volume_percent.rename('Обьем,% 30 минутных интервалов')], axis=1)
        df2=df3.copy()

        flow_rate = st.text_input("введите величину расхода электроэнергии и нажмите Enter (дробную часть через точку):", value="")
        if flow_rate:
            flow_rate=float(flow_rate)  
            df2['Расход по разности показаний, кВт*ч'] = flow_rate

            df2=df2[['Идентификатор ТУ','Расход по разности показаний, кВт*ч']]
            df1=df3.copy()
            df1=df1[['Идентификатор ТУ']]

            df1['нач_показ'] = 'нд'
            df1['кон_показ'] = 'нд'

            result = df1.merge(df2, on='Идентификатор ТУ', how='outer').merge(df3, on='Идентификатор ТУ', how='outer')
            result['НБ, кВт*ч'] = pd.to_numeric(result['Расход по разности показаний, кВт*ч'] - result['Сумма 30 минутных интервалов, кВт*ч'],errors='coerce').round(1)

            result['Примечание'] = result.apply(lambda row: prim(row,file3.loc[file3['Идентификатор ТУ'] == row['Идентификатор ТУ'], date_columns].values.flatten()), axis=1)

            columns = result.columns.tolist()

            nb_index = columns.index('НБ, кВт*ч')

            volume_index = columns.index('Обьем,% 30 минутных интервалов')

            columns[nb_index], columns[volume_index] = columns[volume_index], columns[nb_index]

            result = result[columns]

            result_file_path = os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx')

            styled_result = result.style.apply(color, axis=1)

            styled_result.to_excel(result_file_path, engine='openpyxl', index=False)


            pd.set_option('display.max_columns', None)
            warnings.simplefilter(action='ignore', category=FutureWarning)

            svod=pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx'), decimal=',',dtype='str')
            svod=svod[['Расход по разности показаний, кВт*ч','Сумма 30 минутных интервалов, кВт*ч','Примечание']]
            svod

            # Проверка условия
            if (result['Примечание'] == 'Достоверно').any():
                st.markdown(f'достоверизация не нужна')
                sys.exit(0)  # Завершение программы без ошибок
            else:
                # Продолжение логики программы, если условие не выполнено
                pass  # Здесь может быть ваш код обработки данных
            
            # Загрузка данных
            info = pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx'))
            dates_df = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'))

            values_df = dates_df.merge(info[['Идентификатор ТУ', 'НБ, кВт*ч', 'Примечание']], on='Идентификатор ТУ', how='outer')
            values_df = values_df[values_df['Примечание'] == 'Требуется достоверизация']
            values_df = values_df.drop(columns=['Примечание'])

            # Выделяем только столбцы с данными времени
            date_columns = [col for col in values_df.columns if ":" in col and '.' in col]

            # Преобразуем эти столбцы в числовой формат (пропуски станут NaN) и заполняем пропуски нулями
            values_df[date_columns] = values_df[date_columns].apply(pd.to_numeric, errors='coerce')
            values_df[date_columns] = values_df[date_columns].fillna(0)

            # Применяем корректировку и собираем результаты в список
            corrected_groups = []
            for group_name, group_data in values_df.groupby('Идентификатор ТУ'):
                group_corrected = group_data.copy()

                # Заполняем провалы
                group_corrected[date_columns] = fill_provokes_dynamic(
                group_corrected[date_columns].iloc[0],
                group_corrected['НБ, кВт*ч'].iloc[0]
                )
                corrected_groups.append(group_corrected)

                # Объединяем исправленные группы
                if corrected_groups:  # Убедимся, что есть данные для объединения
                    corrected_df = pd.concat(corrected_groups, ignore_index=True)
                else:
                    print("Нет данных для объединения")
            

                # Сохраняем результат
                corrected_df.pop(corrected_df.columns[-1])
                result_file_path = os.path.join(folder_path, 'шаблон30мин.xlsx')
                corrected_df.to_excel(result_file_path, index=False)

            f1 = file3
            f2 = pd.read_excel(os.path.join(folder_path, 'шаблон30мин.xlsx'), decimal=',')
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

            sum1=ff['стало'].sum()
            st.markdown(f'сумма 30 минуток после коррекции: {sum1}')

            # Создаем график
            fig = px.line(ff, x='дата_время', y=['было', 'стало'],title=f'ТУ: {info.iloc[0,0]}, {f1.iloc[0,1]}, расхождение {info.iloc[0,5]} кВт*ч')

            # Добавляем метки значений к линиям
            fig.update_traces(textposition='top center')
            fig

            st.markdown(f'импортируйте шаблон30мин-{flow_rate}.xlsx из папки {folder_path} в пирамиду и произведите замещение данных по импортированным значениям')
            # Указываем путь до исходного файла
            source_file = os.path.join(folder_path, f'шаблон30мин.xlsx')
            # Открываем файл
            wb = openpyxl.load_workbook(source_file)
            
            # Получаем имя текущего листа
            sheet_name = wb.sheetnames[0]
            ws = wb[sheet_name]

            # Значение переменной, которое нужно добавить к названию файла
            variable_value = f'{flow_rate}'

            # Формируем новое название файла
            new_filename = f'{source_file[:-5]}_{variable_value}.xlsx'

            # Сохраняем копию файла под новым именем
            wb.save(new_filename)
            print(f'Файл {new_filename} успешно создан.')

            fig.write_html(os.path.join(folder_path, f'график-{flow_rate}.html'))

            st.title("достоверизация по 2му варианту:")
            st.markdown('может применяться для точек учета, где имеются провалы более 3-х 30 минуток подряд')
            st.markdown('в шаблоне 30мин необходимо произвести замену "-" на нули')

            # Заданная целевая сумма
            target_sum = flow_rate

            df11 = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'))

            date_columns = [col for col in df11.columns if ":" in col and '.' in col]

            df11[date_columns] = (
                df11[date_columns]
                .replace(["-", "", " "], np.nan)
                .apply(pd.to_numeric, errors='coerce')
                .fillna(0)
            )

            df22=df11.copy()
            dost=df11.T.iloc[4:]
            dost.columns=['value']
            dost['value'] = dost['value'].astype(float)
            # Преобразуем индексы строк в столбец
            dost= dost.reset_index()
            dost.columns=['datetime','value']
            # Определяем шаг, который мы будем использовать для группировки данных (336-неделя, 48 - сутки)
            step = 48
            # Создаем новый датафрейм, где будут храниться сгруппированные данные
            grouped_df = dost.iloc[:len(dost) // step * step].copy()
            grouped_df['group'] = grouped_df.index % step

            # Группируем данные по созданному столбцу 'group'
            groups = grouped_df.groupby('group')

            # Для каждой группы находим минимальное значение и заменяем его средним значением всех остальных значений в группе
            for group_name, group in groups:
                # Находим минимальный индекс внутри группы
                min_value_index_in_group = group['value'].argmin()
        
                # Получаем глобальный индекс строки в датафрейме grouped_df
                global_min_value_index = group.index[min_value_index_in_group]
        
                # Вычисляем среднее значение всех остальных элементов в группе
                mean_of_others = group.loc[group.index != global_min_value_index, 'value'].mean()
        
                # Обновляем значение в датафрейме grouped_df
                grouped_df.at[global_min_value_index, 'value'] = mean_of_others

            # Объединяем измененный датафрейм с оставшимися данными
            result_df = pd.concat([grouped_df, dost.iloc[len(grouped_df):]])

            # Текущая сумма значений в result_df
            current_sum = result_df['value'].sum()

            # Коэффициент корректировки
            correction_factor = target_sum / current_sum

            # Применяем коэффициент к каждому значению в result_df
            result_df['value'] *= correction_factor

            # Проверка новой суммы
            new_sum = result_df['value'].sum()
            print(f"Новая сумма значений: {new_sum}")

            ff1=pd.merge(dost, result_df, on='datetime')
            ff1.columns=['datetime', 'было', 'стало', 'group']

            fig33 = px.line(ff1,x='datetime', y=['было','стало'],title=f"сумма значений: было - {ff['было'].sum()}, стало - {ff['стало'].sum()}")
            fig33


            str_new=result_df[['value']]

            str_new=str_new.T

            df22.iloc[0, 4:] = str_new
            df22.to_excel(os.path.join(folder_path, f'вар2-шаблон-{flow_rate}.xlsx'), index=False)

            st.markdown(f'импортируйте вар2 шаблон30мин-{flow_rate}.xlsx из папки {folder_path} в пирамиду и произведите замещение данных по импортированным значениям')

            fig33.write_html(os.path.join(folder_path, f'вар2-график-{flow_rate}.html'))
            df22

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
                if st.button("Удалить папку", icon=":material/cleaning_bucket:", key="delete_button"):
                    if os.path.exists(DIR_PATH):
                        try:
                            shutil.rmtree(DIR_PATH)
                            st.success(f"Папка '{DIR_PATH}' удалена.")
                        except Exception as e:
                            st.error(f"Ошибка при удалении папки: {str(e)}")
                    else:
                        st.warning(f"Папка '{DIR_PATH}' не найдена.")


            DIR_PATH = f"data/one_pu/{dir_name}"
            output_files(DIR_PATH)
            del_dir(DIR_PATH)