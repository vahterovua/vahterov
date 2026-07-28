import streamlit as st
import os
import numpy as np
import pandas as pd
import warnings
import base64
from PIL import Image
import shutil

# Настройка отображения и предупреждений
pd.set_option('display.max_columns', None)
warnings.simplefilter(action='ignore', category=FutureWarning)

values_porog = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1]

# Виджет selectbox для выбора порога
porog = st.selectbox('Выберите чувствительность:', values_porog)
st.write(f"чувствительность: {porog}")

def count_non_numeric(row):
    return row.isna().sum()

def has_long_sequence_of_dashes(date_vals):
    dash_count = 0
    for val in date_vals:
        if pd.isna(val):
            dash_count += 1
            if dash_count > 3:
                return True
        else:
            dash_count = 0
    return False

def prim(row, date_vals):
    nb_kwh = row.get('НБ, кВт*ч', np.nan)
    sum_intervals = row.get('Сумма 30 минутных интервалов, кВт*ч', np.nan)

    if pd.notna(nb_kwh) and pd.notna(sum_intervals) and nb_kwh > 0.5 * sum_intervals:
        return 'Слишком большое отклонение'

    if has_long_sequence_of_dashes(date_vals):
        return 'Больше трех пропусков'

    # Проверка по индексам только если есть достаточно колонок, иначе пропускаем
    if len(row) >= 6:
        if is_string_dtype(pd.Series([row.iloc[3]])) or row.iloc[3] == '-':
            return 'Отсутствует показание на начало или конец периода'
        if (is_string_dtype(pd.Series([row.iloc[4]])) or is_string_dtype(pd.Series([row.iloc[5]])) or
            pd.isna(row.iloc[4]) or pd.isna(row.iloc[5])):
            return 'Недостаточно данных'

    vol_key = 'Обьем,% 30 минутных интервалов'
    if vol_key in row and row[vol_key] <= 90:
        return 'Недостаточный объем сбора данных'

    nb_key = 'НБ, кВт*ч'
    if nb_key in row:
        nb_val = row[nb_key]
        vol_val = row.get(vol_key, 0)
        if nb_val != 0 or (nb_val == 0 and vol_val != 100):
            return 'Требуется достоверизация'

    return 'Достоверно'

def color(row):
    styles = [''] * len(row)
    idx_map = {name: row.index.get_loc(name) for name in row.index if name in ['НБ, кВт*ч', 'Обьем,% 30 минутных интервалов', 'Примечание']}

    if 'НБ, кВт*ч' in idx_map and row['НБ, кВт*ч'] == 0:
        styles[idx_map['НБ, кВт*ч']] = 'background-color: #c6efce'

    if 'Обьем,% 30 минутных интервалов' in idx_map and row['Обьем,% 30 минутных интервалов'] == 100:
        styles[idx_map['Обьем,% 30 минутных интервалов']] = 'background-color: #c6efce'

    if 'Примечание' in idx_map:
        note_val = row['Примечание']
        if note_val == 'Достоверно':
            styles[idx_map['Примечание']] = 'background-color: #c6efce'
        elif note_val == 'Требуется достоверизация':
            styles[idx_map['Примечание']] = 'background-color: #ffeb9c'

    return styles

def fill_provokes_dynamic(values_row, nb, threshold):
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

        denom_prev = max(prev_val, 1)
        denom_next = max(next_val, 1)

        if abs(curr_val - prev_val) / denom_prev > threshold and \
           abs(curr_val - next_val) / denom_next > threshold:
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

def check_files_exist(folder_path, filenames):
    if not os.path.exists(folder_path):
        return False
    files_in_folder = os.listdir(folder_path)
    return all(filename in files_in_folder for filename in filenames)

def upload_files(folder_path):
    uploaded_files = st.file_uploader("Выберите файлы для загрузки", accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(folder_path, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.success(f"{len(uploaded_files)} файлов успешно загружены в папку '{folder_path}'.")
    else:
        st.info("Файлы еще не были выбраны.")

st.title("new_достоверизация-опытная эксплуатация")
st.text("- преимущественно подходит для точек учета со стабильным графиком нагрузки")
st.text("- например, базовые станции сотовых сетей, освещение дорог")
st.text("поиск резких уменьшений 30 минуток и заполнение средним значением")
st.text("между предыдущей и следующей 30 минутками")
st.text("в результате обработки формируется файл import для загрузки в Пирамиду 2.0, содержит только скорректированные 30 минутки")

if "dir_name" not in st.session_state:
    st.session_state.dir_name = "default_run"

dir_name = st.session_state.dir_name
folder_path = f'data/{dir_name}'

if not os.path.exists(folder_path):
    os.makedirs(folder_path)

st.markdown("**Порядок действий:**")
st.markdown("1. Выгрузить отчёты из Пирамиды за предыдущий месяц и переименовать их:")
st.markdown("- 30мин.xlsx")
st.markdown("- мес.xlsx")
st.markdown("- сут.xlsx")
st.markdown("2. Загрузить все три файла.")
st.markdown("3. Дождаться сообщения 'Обработка завершена'.")

st.subheader("Загрузить файлы")
upload_files(folder_path)

if st.button("Обработать", key="processing"):
    required_filenames = ["30мин.xlsx", "мес.xlsx", "сут.xlsx"]
    if not check_files_exist(folder_path, required_filenames):
        st.error(f"Загружены не все файлы! Загрузите файлы: {required_filenames}")
    else:
        file1 = pd.read_excel(os.path.join(folder_path, 'сут.xlsx'), decimal=',')
        file2 = pd.read_excel(os.path.join(folder_path, 'мес.xlsx'), decimal=',')
        file3 = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'), decimal=',')

        date_columns = [col for col in file3.columns if ":" in col and "." in col]

        file3[date_columns] = file3[date_columns].replace(["-", "", " "], np.nan).apply(pd.to_numeric, errors='coerce')

        sum_30_min_intervals = file3[date_columns].sum(axis=1)
        volume_percent = (((len(date_columns)) - file3[date_columns].apply(count_non_numeric, axis=1)) / len(date_columns) * 100).round(1)

        df3 = pd.concat([
            file3[['Идентификатор ТУ']],
            sum_30_min_intervals.rename('Сумма 30 минутных интервалов, кВт*ч'),
            volume_percent.rename('Обьем,% 30 минутных интервалов')
        ], axis=1)

        if len(file1.columns) < 5:
            st.error("Файл сут.xlsx имеет неподходящий формат (недостаточно колонок).")
            raise ValueError("Некорректный формат файла сут.xlsx")
        df1 = file1.iloc[:, [0, 1, 4, -1]]

        if len(file2.columns) < 5:
            st.error("Файл мес.xlsx имеет неподходящий формат (недостаточно колонок).")
            raise ValueError("Некорректный формат файла мес.xlsx")
        df2 = file2.iloc[:, [0, 4]].rename(columns={file2.columns[4]: 'Расход по разности показаний, кВт*ч'})

        df2['Расход по разности показаний, кВт*ч'] = pd.to_numeric(df2['Расход по разности показаний, кВт*ч'], errors='coerce').round(1)

        result = df1.merge(df2, on='Идентификатор ТУ', how='outer').merge(df3, on='Идентификатор ТУ', how='outer')

        result['НБ, кВт*ч'] = (result['Расход по разности показаний, кВт*ч'] - result['Сумма 30 минутных интервалов, кВт*ч']).round(1)

        def make_note(row):
            row_dates = file3[file3['Идентификатор ТУ'] == row['Идентификатор ТУ']]
            if row_dates.empty:
                date_vals = []
            else:
                row_dates_vals = row_dates[date_columns].iloc[0].values
                date_vals = row_dates_vals
            return prim(row, date_vals)

        result['Примечание'] = result.apply(make_note, axis=1)

        columns = result.columns.tolist()
        if 'НБ, кВт*ч' in columns and 'Обьем,% 30 минутных интервалов' in columns:
            nb_index = columns.index('НБ, кВт*ч')
            vol_index = columns.index('Обьем,% 30 минутных интервалов')
            columns[nb_index], columns[vol_index] = columns[vol_index], columns[nb_index]
            result = result[columns]

        result_file_path = os.path.join(folder_path, 'Отчет_о_достоверизации_new.xlsx')
        styled_result = result.style.apply(color, axis=1)
        styled_result.to_excel(result_file_path, engine='openpyxl', index=False)

        info = pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации_new.xlsx'))
        dates_df = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'))

        values_df = dates_df.merge(
            info[['Идентификатор ТУ', 'НБ, кВт*ч', 'Примечание']],
            on='Идентификатор ТУ',
            how='outer'
        )

        values_df = values_df[values_df['Примечание'] == 'Требуется достоверизация']

        if values_df.empty:
            st.warning("Нет строк, требующих достоверизации. Файлы коррекции не будут созданы.")
        else:
            values_df = values_df.drop(columns=['Примечание'], errors='ignore')
            date_columns_corr = [col for col in values_df.columns if ":" in col and "." in col]
            if not date_columns_corr:
                st.error("Не найдены временные колонки для коррекции (формат файла 30мин.xlsx отличается).")
                raise ValueError("Нет временных колонок для коррекции")

            values_df[date_columns_corr] = values_df[date_columns_corr].apply(pd.to_numeric, errors='coerce')
            values_df[date_columns_corr] = values_df[date_columns_corr].fillna(0)

            corrected_groups = []
            changes_only_df = pd.DataFrame()
            additional_columns = ['Идентификатор ТУ', 'ТУ', 'Идентификатор параметра', 'Параметр']

            for group_name, group_data in values_df.groupby('Идентификатор ТУ', sort=False):
                group_corrected = group_data.copy()
                row_values = group_corrected[date_columns_corr].iloc[0]
                nb_val = float(group_corrected['НБ, кВт*ч'].iloc[0]) if pd.notna(group_corrected['НБ, кВт*ч'].iloc[0]) else 0.0

                corrected_row = fill_provokes_dynamic(row_values, nb_val, porog)

                # Присваиваем по значениям, чтобы избежать KeyError
                group_corrected.loc[group_data.index[0], date_columns_corr] = corrected_row.values

                diff_mask = group_corrected[date_columns_corr] != group_data[date_columns_corr]
                diff_rows = group_corrected[diff_mask.any(axis=1)].copy()

                if not diff_rows.empty:
                    for col in additional_columns:
                        if col in group_data.columns:
                            diff_rows[col] = group_data[col].iloc[0]
                    changes_only_df = pd.concat([changes_only_df, diff_rows], ignore_index=True)

                corrected_groups.append(group_corrected)

            if corrected_groups:
                corrected_df = pd.concat(corrected_groups, ignore_index=True)
                corrected_df = corrected_df.drop(columns=['НБ, кВт*ч'], errors='ignore')
                result_file_path_getchasovki = os.path.join(folder_path, 'Получасовки_new.xlsx')
                corrected_df.to_excel(result_file_path_getchasovki, index=False)

            changes_only_df = changes_only_df.drop(columns=['НБ, кВт*ч'], errors='ignore')
            result_changes_file_path = os.path.join(folder_path, f'import_{porog}.xlsx')
            changes_only_df.to_excel(result_changes_file_path, index=False)

            st.markdown(f'Обработка завершена, чувствительность: {porog}, вот отчёт о достоверизации')
            st.dataframe(styled_result)
            st.markdown("Файлы доступны в папке `data/{dir_name}` или могут быть добавлены кнопки скачивания при необходимости.")

st.session_state.porog = porog
