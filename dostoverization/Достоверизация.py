import streamlit as st
import os
import numpy as np
import pandas as pd
import warnings
import base64
from PIL import Image
from pandas.api.types import is_string_dtype

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


def prim(row, date_cols_values_flat):
    nb_kwh = row.get('НБ, кВт*ч', np.nan)
    sum_intervals = row.get('Сумма 30 минутных интервалов, кВт*ч', np.nan)

    if pd.notna(nb_kwh) and pd.notna(sum_intervals) and nb_kwh > 0.5 * sum_intervals:
        return 'Слишком большое отклонение'
    elif has_long_sequence_of_dashes(date_cols_values_flat):
        return 'Больше трех пропусков'
    # Осторожно с iloc: если структура изменится, индексы могут не совпасть.
    # Оставляем как в оригинале, но лучше по именам колонок.
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
    if value == 'Требуется достоверизация':
        return 'background-color: #ffeb9c'
    elif value == 'Достоверно':
        return 'background-color: #c6efce'
    else:
        return ''


def color(row):
    styles = [''] * len(row)
    col_names = row.index.tolist()

    if 'НБ, кВт*ч' in col_names:
        nb_idx = col_names.index('НБ, кВт*ч')
        if row['НБ, кВт*ч'] == 0:
            styles[nb_idx] = 'background-color: #c6efce'

    if 'Обьем,% 30 минутных интервалов' in col_names:
        vol_idx = col_names.index('Обьем,% 30 минутных интервалов')
        if row['Обьем,% 30 минутных интервалов'] == 100:
            styles[vol_idx] = 'background-color: #c6efce'

    if 'Примечание' in col_names:
        note_idx = col_names.index('Примечание')
        if row['Примечание'] == 'Достоверно':
            styles[note_idx] = 'background-color: #c6efce'
        elif row['Примечание'] == 'Требуется достоверизация':
            styles[note_idx] = 'background-color: #ffeb9c'

    return styles


def fill_provokes_dynamic(values_row, nb):
    """
    Корректирует данные с учетом провалов, основываясь на динамическом подходе.
    Возвращает pd.Series с теми же индексами, что и values_row.
    """
    values = values_row.values
    corrected = values.copy()

    overall_mean = np.mean(values)
    if np.isnan(overall_mean) or overall_mean == 0:
        overall_mean = 1.0

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

        denom_prev = max(prev_val, 1e-9)
        denom_next = max(next_val, 1e-9)

        if abs(curr_val - prev_val) / denom_prev > 0.5 and abs(curr_val - next_val) / denom_next > 0.5:
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


def check_files_exist(folder_path, filenames):
    if not os.path.exists(folder_path):
        return False
    files_in_folder = os.listdir(folder_path)
    return all(filename in files_in_folder for filename in filenames)


def upload_files(folder_path):
    uploaded_files = st.file_uploader("Выберите файлы для загрузки", accept_multiple_files=True)
    if uploaded_files is not None:
        for file in uploaded_files:
            with open(os.path.join(folder_path, file.name), "wb") as f:
                f.write(file.getbuffer())
        if len(uploaded_files) > 0:
            st.success(f"{len(uploaded_files)} файлов успешно загружены в папку '{folder_path}'.")
    else:
        st.info("Файлы еще не были выбраны.")


st.title("Достоверизация")

if "dir_name" not in st.session_state:
    st.session_state["dir_name"] = "default_run"

dir_name = st.session_state.dir_name
folder_path = f'data/{dir_name}'

if not os.path.exists(folder_path):
    os.makedirs(folder_path)

st.markdown("""**Порядок действий:**""")
st.markdown("""1. Выгрузить отчёты из «Пирамиды» за предыдущий месяц и переименовать их в:""")
st.markdown("""- `30мин.xlsx`""")
st.markdown("""- `мес.xlsx`""")
st.markdown("""- `сут.xlsx`""")
st.markdown("""2. Загрузить все 3 файла через форму ниже.""")
st.markdown("""3. Нажать кнопку «Обработать».""")
st.markdown("""4. Дождаться сообщения «Обработка завершена».""")

st.subheader("Загрузить файлы")
upload_files(folder_path)

if st.button("Обработать", key="processing"):
    required_filenames = ["30мин.xlsx", "мес.xlsx", "сут.xlsx"]

    if not check_files_exist(folder_path, required_filenames):
        st.error(f"Загружены не все файлы! Пожалуйста, загрузите файлы: {required_filenames}")
    else:
        try:
            file1 = pd.read_excel(os.path.join(folder_path, 'сут.xlsx'), decimal=',')
            file2 = pd.read_excel(os.path.join(folder_path, 'мес.xlsx'), decimal=',')
            file3 = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'), decimal=',')

            date_columns = [col for col in file3.columns if ":" in str(col) and "." in str(col)]

            if len(date_columns) == 0:
                # Пробуем более мягкий критерий, если жесткий не сработал
                date_columns = [col for col in file3.columns if ":" in str(col)]

            if len(date_columns) == 0:
                st.error("Не найдены колонки с временными метками в файле '30мин.xlsx'. Проверьте формат названий колонок.")
                raise ValueError("Нет колонок с временными данными")

            file3[date_columns] = file3[date_columns].replace(["-", "", " "], np.nan).apply(pd.to_numeric, errors='coerce')

            sum_30_min_intervals = file3[date_columns].sum(axis=1)
            volume_percent = (((len(date_columns)) - file3[date_columns].apply(count_non_numeric, axis=1)) / len(date_columns) * 100).round(1)

            df3 = pd.concat([
                file3[['Идентификатор ТУ']],
                sum_30_min_intervals.rename('Сумма 30 минутных интервалов, кВт*ч'),
                volume_percent.rename('Обьем,% 30 минутных интервалов')
            ], axis=1)

            df1 = file1.iloc[:, [0, 1, 4, -1]]
            df2 = file2.iloc[:, [0, 4]].rename(columns={file2.columns[4]: 'Расход по разности показаний, кВт*ч'})
            df2['Расход по разности показаний, кВт*ч'] = pd.to_numeric(df2['Расход по разности показаний, кВт*ч'], errors='coerce').round(1)

            result = df1.merge(df2, on='Идентификатор ТУ', how='outer').merge(df3, on='Идентификатор ТУ', how='outer')
            result['НБ, кВт*ч'] = pd.to_numeric(
                result['Расход по разности показаний, кВт*ч'] - result['Сумма 30 минутных интервалов, кВт*ч'],
                errors='coerce'
            ).round(1)

            result['Примечание'] = result.apply(
                lambda row: prim(
                    row,
                    file3.loc[file3['Идентификатор ТУ'] == row['Идентификатор ТУ'], date_columns].values.flatten()
                ),
                axis=1
            )

            columns = result.columns.tolist()
            if 'НБ, кВт*ч' in columns and 'Обьем,% 30 минутных интервалов' in columns:
                nb_index = columns.index('НБ, кВт*ч')
                volume_index = columns.index('Обьем,% 30 минутных интервалов')
                columns[nb_index], columns[volume_index] = columns[volume_index], columns[nb_index]
                result = result[columns]

            result_file_path_report = os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx')
            styled_result = result.style.apply(color, axis=1)
            styled_result.to_excel(result_file_path_report, engine='openpyxl', index=False)

            # --- Блок коррекции получасовок ---
            info = pd.read_excel(os.path.join(folder_path, 'Отчет_о_достоверизации.xlsx'))
            dates_df = pd.read_excel(os.path.join(folder_path, '30мин.xlsx'))

            values_df = dates_df.merge(
                info[['Идентификатор ТУ', 'НБ, кВт*ч', 'Примечание']],
                on='Идентификатор ТУ',
                how='outer'
            )
            values_df = values_df[values_df['Примечание'] == 'Требуется достоверизация']
            values_df = values_df.drop(columns=['Примечание'], errors='ignore')

            date_columns_corr = [col for col in values_df.columns if ":" in str(col) and "." in str(col)]
            if len(date_columns_corr) == 0:
                date_columns_corr = [col for col in values_df.columns if ":" in str(col)]

            if len(date_columns_corr) == 0:
                st.warning("Не удалось автоматически определить колонки с получасовками для коррекции. Файл 'Получасовки.xlsx' не будет создан.")
            else:
                values_df[date_columns_corr] = values_df[date_columns_corr].apply(pd.to_numeric, errors='coerce')
                values_df[date_columns_corr] = values_df[date_columns_corr].fillna(0)

                corrected_groups = []
                for group_name, group_data in values_df.groupby('Идентификатор ТУ', sort=False):
                    group_corrected = group_data.copy()
                    if len(group_corrected) == 0:
                        continue

                    first_row_index = group_corrected.index[0]
                    row_values = group_corrected.loc[first_row_index, date_columns_corr]
                    nb_value = group_corrected.loc[first_row_index, 'НБ, кВт*ч']

                    if pd.isna(nb_value) or nb_value < 0:
                        corrected_row = row_values.copy()
                    else:
                        corrected_row = fill_provokes_dynamic(row_values, nb_value)

                    # Безопасное присваивание по индексу
                    group_corrected.loc[first_row_index, date_columns_corr] = corrected_row.values
                    corrected_groups.append(group_corrected)

                if corrected_groups:
                    corrected_df = pd.concat(corrected_groups, ignore_index=True)
                    result_file_path_corr = os.path.join(folder_path, 'Получасовки.xlsx')
                    corrected_df.to_excel(result_file_path_corr, index=False)
                    st.text(f'Обработано {len(corrected_df)} точек.')
                else:
                    st.warning("Нет точек, требующих коррекции (или все точки достоверны).")

            st.markdown("**Обработка завершена.**")
            st.markdown("Файл «Отчет_о_достоверизации.xlsx» создан.")
            if os.path.exists(os.path.join(folder_path, 'Получасовки.xlsx')):
                st.markdown("Файл «Получасовки.xlsx» (с коррекцией) также создан.")

        except Exception as e:
            st.error(f"Произошла ошибка при обработке: {str(e)}")
            st.exception(
