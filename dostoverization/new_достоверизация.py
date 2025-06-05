import streamlit as st
import os
import numpy as np
import pandas as pd
import os
import logging
from pandas.api.types import is_string_dtype
import warnings
import streamlit as st
import os
import base64
from PIL import Image
import shutil

values_porog = [0.5,0.45,0.4,0.35,0.3,0.25,0.2,0.15,0.1]

# Виджет selectbox для выбора порога
porog = st.selectbox('Выберите чувствительность:', values_porog)

# Выведем выбранное значение порога
st.write(f"чувствительность: {porog}")


pd.set_option('display.max_columns', None)
warnings.simplefilter(action='ignore', category=FutureWarning)

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

        if abs(curr_val - prev_val) / max(prev_val, 1) > porog and abs(curr_val - next_val) / max(next_val, 1) > porog:
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

    return pd.Series(corrected, index=values_row.index)

def download_file(filename):
    with open(filename, "rb") as f:
        bytes_data = f.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:file/{filename};base64,{b64}" download="{filename}">{filename}</a>'
    return href

def check_files_exist(folder_path, filenames):
    files_in_folder = os.listdir(folder_path)
    return all(filename in files_in_folder for filename in filenames)

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

st.title("new_достоверизация-опытная эксплуатация")
st.text("- преимущественно подходит для точек учета со стабильным графмиком нагрузки")
st.text("- например, базовые станции сотовых сетей, освещение дорог")
st.text("поиск резких уменьшений 30 минуток и заполнение средним значением")
st.text("между предыдущей и следующей 30 минутками")
st.text("в результате обработки формируется файл import для загрузки в Пирамиду 2.0, содержит только скорректированные 30 минутки")


if "dir_name" in st.session_state:
    dir_name = st.session_state.dir_name
    folder_path = f'data/{dir_name}'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    st.markdown("""**Порядок действий:**""")
    st.markdown("""1. Выгрузить отчёты из пирамиды за предыдущий месяц и переименовать их:""")
    st.markdown(""" - 30 мин.xlsx""")
    st.markdown(""" - мес.xlsx""")
    st.markdown(""" - сут.xlsx""")
    st.markdown("""3. Загрузить все три файла.""")
    st.markdown("""4. Дождаться сообщения 'Обработка завершена'. """)
    st.title("Загрузить файлы")

    upload_files()

if st.button("Обработать", key="processing"):
    required_filenames = ["30мин.xlsx", "мес.xlsx", "сут.xlsx"]
    if check_files_exist(folder_path, required_filenames):
        file1 = pd.read_excel(os.path.join(folder_path, 'сут.xlsx'), decimal=',')
        file2 = pd.read_excel(os.path.join(folder_path, 'мес.xlsx'), decimal=',')
        file3 = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'), decimal=',')

        date_columns = [col for col in file3.columns if ":" in col and '.' in col]

        file3[date_columns] = file3[date_columns].replace(["-", "", " "], np.nan).apply(pd.to_numeric, errors='coerce')

        sum_30_min_intervals = file3[date_columns].sum(axis=1)

        volume_percent = (((len(date_columns)) - file3[date_columns].apply(count_non_numeric, axis=1)) / len(date_columns) * 100).round(1)

        df3 = pd.concat([file3[['Идентификатор ТУ']], sum_30_min_intervals.rename('Сумма 30 минутных интервалов, кВт*ч'), volume_percent.rename('Обьем,% 30 минутных интервалов')], axis=1)

        df1 = file1.iloc[:, [0, 1, 4, -1]]

        df2 = file2.iloc[:, [0, 4]].rename(columns={file2.columns[4]: 'Расход по разности показаний, кВт*ч'})

        df2['Расход по разности показаний, кВт*ч'] = pd.to_numeric(df2['Расход по разности показаний, кВт*ч'], errors='coerce').round(1)

        result = df1.merge(df2, on='Идентификатор ТУ', how='outer').merge(df3, on='Идентификатор ТУ', how='outer')

        result['НБ, кВт*ч'] = pd.to_numeric(result['Расход по разности показаний, кВт*ч'] - result['Сумма 30 минутных интервалов, кВт*ч'], errors='coerce').round(1)

        result['Примечание'] = result.apply(lambda row: prim(row, file3.loc[file3['Идентификатор ТУ'] == row['Идентификатор ТУ'], date_columns].values.flatten()), axis=1)

        columns = result.columns.tolist()
        nb_index = columns.index('НБ, кВт*ч')
        volume_index = columns.index('Обьем,% 30 минутных интервалов')
        columns[nb_index], columns[volume_index] = columns[volume_index], columns[nb_index]
        result = result[columns]

        result_file_path = os.path.join(folder_path, 'Отчет_о_достоверизации_new.xlsx')

        styled_result = result.style.apply(color, axis=1)
        styled_result.to_excel(result_file_path, engine='openpyxl', index=False)

        # Загрузка данных
        info = pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации_new.xlsx'))
        dates_df = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'))

        values_df = dates_df.merge(info[['Идентификатор ТУ', 'НБ, кВт*ч', 'Примечание']], on='Идентификатор ТУ', how='outer')
        values_df = values_df[values_df['Примечание'] == 'Требуется достоверизация']
        values_df = values_df.drop(columns=['Примечание'])

        # Выделяем только столбцы с временными метками
        date_columns = [col for col in values_df.columns if ":" in col and '.' in col]

        # Преобразуем временные столбцы в числовой формат и заполняем пропуска нулями
        values_df[date_columns] = values_df[date_columns].apply(pd.to_numeric, errors='coerce')
        values_df[date_columns] = values_df[date_columns].fillna(0)

        # Сборка изменённых строк
        corrected_groups = []
        original_values = []
        changes_only_df = pd.DataFrame()

        # Группа по идентификатору прибора учёта
        for group_name, group_data in values_df.groupby('Идентификатор ТУ'):
            group_corrected = group_data.copy()

            # Выполняем коррекцию
            group_corrected[date_columns] = fill_provokes_dynamic(
                group_corrected[date_columns].iloc[0],
                group_corrected['НБ, кВт*ч'].iloc[0]
            )

            # Сохраняем оригинал
            original_values.append(group_data)

            # Извлекаем изменённые строки
            diff_rows = group_corrected.where(group_data != group_corrected, other=np.nan).dropna(how='all')

            # Дополняем изменённые строки дополнительными столбцами
            additional_columns = ['Идентификатор ТУ', 'ТУ', 'Идентификатор параметра', 'Параметр']
            for column in additional_columns:
                if column in group_data.columns:
                    diff_rows[column] = group_data[column].iloc[0]

            # Собираем изменённые строки
            changes_only_df = pd.concat([changes_only_df, diff_rows], ignore_index=True)

            # Добавляем исправленную версию
            corrected_groups.append(group_corrected)

        # Объединяем исправленные группы
        if corrected_groups:
            corrected_df = pd.concat(corrected_groups, ignore_index=True)
        else:
            print("Нет данных для объединения")

        # Убираем столбец 'НБ,кВт*ч' перед записью в файл
        corrected_df = corrected_df.drop(columns=['НБ, кВт*ч'])
        result_file_path_getchasovki = os.path.join(folder_path, 'Получасовки_new.xlsx')
        corrected_df.to_excel(result_file_path_getchasovki, index=False)
        #st.text(f'обработано {len(corrected_df)} точек')

        # Аналогично делаем для файла с изменениями
        changes_only_df = changes_only_df.drop(columns=['НБ, кВт*ч'], errors='ignore')
        result_changes_file_path = os.path.join(folder_path, f'import_{porog}.xlsx')
        changes_only_df.to_excel(result_changes_file_path, index=False)

        # Отчёт о выполнении
        st.markdown(f'Обработка завершена, чувствительность: {porog} , вот отчёт о достоверизации')
        styled_result

        st.markdown("""Файл для скачивания находится во вкладке 'Просмотр файлов'""")
    else:
        st.error(f"""Загружены не все файлы! Загрузите файлы: {required_filenames}""")

st.session_state.porog = porog