import pandas as pd
import numpy as np
import streamlit as st
import os

def fill_provokes_dynamic(row, nb_value):
    """
    Функция для коррекции данных.
    Замените на вашу реальную функцию.
    """
    # Пример реализации - замените на вашу логику
    corrected = row.copy()
    # Ваша логика коррекции
    # Например, если значение превышает порог, заменяем на среднее
    for i in range(len(corrected)):
        if corrected.iloc[i] > nb_value * 1.5:
            corrected.iloc[i] = nb_value / 24  # Примерное распределение
    return corrected

def color(row):
    """
    Функция для стилизации отчета.
    Замените на вашу логику окрашивания.
    """
    return ['background-color: lightgreen' if row['Статус'] == 'Успешно' else 'background-color: lightcoral' for _ in row]

# Основной код обработки
def process_data(folder_path, porog):
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
        
        # Получаем результат коррекции
        corrected_values = fill_provokes_dynamic(
            group_corrected[date_columns].iloc[0],
            group_corrected['НБ, кВт*ч'].iloc[0]
        )
        
        # Убеждаемся, что результат - это Series с правильным индексом
        if isinstance(corrected_values, (list, np.ndarray)):
            # Если это массив, преобразуем в Series с индексом date_columns
            corrected_series = pd.Series(corrected_values, index=date_columns)
        elif isinstance(corrected_values, pd.Series):
            # Если это Series, убеждаемся что индекс правильный
            corrected_series = corrected_values
            if not corrected_series.index.equals(date_columns):
                corrected_series.index = date_columns
        else:
            # Если это DataFrame или что-то другое
            corrected_series = pd.Series(corrected_values, index=date_columns)
        
        # Присваиваем значения, убедившись, что они в правильном формате
        for col in date_columns:
            if col in corrected_series.index:
                group_corrected[col] = corrected_series[col]
            else:
                # Если столбца нет в результате, используем оригинальное значение
                group_corrected[col] = group_data[col].iloc[0]
        
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
        
        # Добавляем исправлен

        corrected_groups.append(group_corrected)
    
    # Объединяем исправленные группы
    if corrected_groups:
        corrected_df = pd.concat(corrected_groups, ignore_index=True)
    else:
        print("Нет данных для объединения")
        return None, None, None
    
    # Убираем столбец 'НБ,кВт*ч' перед записью в файл
    corrected_df = corrected_df.drop(columns=['НБ, кВт*ч'], errors='ignore')
    result_file_path_getchasovki = os.path.join(folder_path, 'Получасовки_new.xlsx')
    corrected_df.to_excel(result_file_path_getchasovki, index=False)
    
    # Аналогично делаем для файла с изменениями
    changes_only_df = changes_only_df.drop(columns=['НБ, кВт*ч'], errors='ignore')
    result_changes_file_path = os.path.join(folder_path, f'import_{porog}.xlsx')
    changes_only_df.to_excel(result_changes_file_path, index=False)
    
    # Создание отчета
    result = info.copy()
    styled_result = result.style.apply(color, axis=1)
    styled_result.to_excel(os.path.join(folder_path, 'Отчет_о_достоверизации_new.xlsx'), engine='openpyxl', index=False)
    
    return corrected_df, changes_only_df, styled_result

# Streamlit интерфейс
def main():
    st.title("Достоверизация данных")
    
    # Настройка параметров
    porog = st.slider("Выберите чувствительность", min_value=1, max_value=100, value=50)
    st.session_state.porog = porog
    
    folder_path = st.text_input("Укажите путь к папке с файлами")
    
    required_filenames = ['Отчет_о_достоверизации_new.xlsx', '30мин.xlsx']
    
    if st.button("Обработать данные"):
        if all(os.path.exists(os.path.join(folder_path, f)) for f in required_filenames):
            try:
                corrected_df, changes_only_df, styled_result = process_data(folder_path, porog)
                
                if corrected_df is not None:
                    st.markdown(f'Обработка завершена, чувствительность: {porog}, вот отчёт о достоверизации')
                    st.dataframe(corrected_df.head())
                    st.markdown("""Файл для скачивания находится во вкладке 'Просмотр файлов'""")
                else:
                    st.warning("Нет данных для обработки")
                    
            except Exception as e:
                st.error(f"Произошла ошибка: {str(e)}")
                print(f"Ошибка: {e}")
        else:
            st.error(f"""Загружены не все файлы! Загрузите файлы: {required_filenames}""")

# Запуск приложения
if __name__ == "__main__":
    main()
