import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time
import re
import os
import io
from scipy.sparse.csgraph import connected_components

# Настройка страницы
st.set_page_config(
    page_title="Анализ напряжений 10-минутных срезов",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Анализ данных напряжения (U10min) - ver 180226")
#st.markdown("Веб-приложение для анализа фазных напряжений по объектам Вороновки и Дятлово")

# Боковая панель для загрузки файла
with st.sidebar:
    st.header("Загрузка данных")
    uploaded_file = st.file_uploader("Выберите CSV-файл (формат как в шаблоне)", type=["csv"])
    
    if uploaded_file is not None:
        file_to_use = uploaded_file
        st.success(f"Загружен файл: {uploaded_file.name}")
    else:
        local_path = st.text_input("Или укажите путь к локальному файлу-шаблону:", value="шаблон_10мин.csv")
        if os.path.exists(local_path):
            file_to_use = local_path
            st.info(f"Используется локальный файл: {local_path}")
        else:
            st.error(f"Файл '{local_path}' не найден. Пожалуйста, загрузите файл или укажите правильный путь.")
            st.stop()
    
    st.subheader("Параметры анализа")
    min_alarm = st.slider("Порог минимального напряжения (тревога), В", 190, 220, 210)
    max_alarm = st.slider("Порог максимального напряжения (тревога), В", 230, 250, 240)
    asymmetry_threshold = st.slider("Порог несимметрии фаз (ΔU), В", 5, 30, 10)
    
    st.subheader("Параметры корреляции")
    corr_method = st.selectbox("Метод корреляции", ["pearson", "spearman"], index=0)
    corr_threshold = st.slider("Минимальный порог отображения корреляции", 0.0, 1.0, 0.7, 0.05)
    
    st.subheader("Параметры группировки каналов")
    cluster_threshold = st.slider("Порог корреляции для группировки (каналы считаются связанными)", 0.0, 1.0, 0.9, 0.01)
    
    # Скрытые настройки зон суток (по умолчанию свёрнуты)
    with st.expander("Границы зон суток (часы)", expanded=False):
        night_start = st.slider("Начало ночи", 0, 23, 0, 1)
        night_end = st.slider("Конец ночи", 0, 23, 5, 1)
        morning_start = st.slider("Начало утра", 0, 23, 5, 1)
        morning_end = st.slider("Конец утра", 0, 23, 11, 1)
        day_start = st.slider("Начало дня", 0, 23, 11, 1)
        day_end = st.slider("Конец дня", 0, 23, 17, 1)
        evening_start = st.slider("Начало вечера", 0, 23, 17, 1)
        evening_end = st.slider("Конец вечера", 0, 23, 23, 1)

# Функция парсинга названия канала
def parse_channel(name):
    name = str(name).strip()
    settlement = "Неизвестно"
    if '_' in name:
        after_underscore = name.split('_', 1)[1]
        if ',' in after_underscore:
            settlement = after_underscore.split(',')[0].strip()
    else:
        if ',' in name:
            settlement = name.split(',')[0].strip()
    
    phase = '0'
    if 'фаза 1' in name.lower():
        phase = '1'
    elif 'фаза 2' in name.lower():
        phase = '2'
    elif 'фаза 3' in name.lower():
        phase = '3'
    return settlement, phase

# Загрузка данных
@st.cache_data
def load_data(file):
    if isinstance(file, str):
        df = pd.read_csv(file, index_col=0, parse_dates=True, encoding='utf-8', dayfirst=True)
    else:
        df = pd.read_csv(file, index_col=0, parse_dates=True, encoding='utf-8', dayfirst=True)
    # Принудительное преобразование индекса в datetime, если не удалось
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, dayfirst=True, errors='coerce')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(axis=1, how='all')
    return df

df = load_data(file_to_use)

# Парсим информацию о каналах
channel_info = {}
for col in df.columns:
    settlement, phase = parse_channel(col)
    channel_info[col] = {"settlement": settlement, "phase": phase}

meta_df = pd.DataFrame.from_dict(channel_info, orient='index')
meta_df.index.name = 'Канал'

# Функция для разбиения по зонам суток
def get_time_of_day(dt):
    hour = dt.hour
    if night_start <= hour < night_end or (night_end < night_start and (hour >= night_start or hour < night_end)):
        return 'Ночь'
    elif morning_start <= hour < morning_end or (morning_end < morning_start and (hour >= morning_start or hour < morning_end)):
        return 'Утро'
    elif day_start <= hour < day_end or (day_end < day_start and (hour >= day_start or hour < day_end)):
        return 'День'
    elif evening_start <= hour < evening_end or (evening_end < evening_start and (hour >= evening_start or hour < evening_end)):
        return 'Вечер'
    else:
        return 'Неопределено'

# Добавляем столбец с зоной суток
df['time_of_day'] = df.index.to_series().apply(get_time_of_day)

# Основные вкладки
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 Общая информация",
    "🔍 Качество данных",
    "📈 Временные ряды",
    "📊 Статистика и распределение",
    "⚠️ Аномалии",
    "🔗 Корреляционный анализ",
    "💡 Рекомендации"
])

# ==================== TAB 1: Общая информация ====================
with tab1:
    st.header("Общая характеристика данных")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Количество каналов (объектов)", len(df.columns)-1)  # вычитаем time_of_day
    with col2:
        st.metric("Количество временных меток", len(df))
    with col3:
        st.metric("Период измерений", f"{df.index.min().strftime('%d.%m.%Y %H:%M')} - {df.index.max().strftime('%d.%m.%Y %H:%M')}")
    
    st.subheader("Распределение каналов по населённым пунктам")
    settlement_counts = meta_df['settlement'].value_counts()
    fig = px.bar(x=settlement_counts.index, y=settlement_counts.values, 
                 labels={'x':'Населённый пункт', 'y':'Количество каналов'},
                 color=settlement_counts.values, color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Распределение каналов по фазам")
    phase_counts = meta_df['phase'].map({'0':'Одна фаза', '1':'Фаза 1', '2':'Фаза 2', '3':'Фаза 3'}).value_counts()
    fig = px.pie(values=phase_counts.values, names=phase_counts.index, title='Типы каналов')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Пример данных (первые строки)")
    st.dataframe(df.drop(columns=['time_of_day']).head(10))

# ==================== TAB 2: Качество данных ====================
with tab2:
    st.header("Анализ качества данных")
    
    missing_by_time = df.drop(columns=['time_of_day']).isnull().sum(axis=1)
    st.subheader("Количество пропусков по временным меткам")
    fig = px.bar(x=df.index, y=missing_by_time.values, 
                  labels={'x':'Время', 'y':'Количество пропусков'})
    st.plotly_chart(fig, use_container_width=True)
    
    completeness = (1 - df.drop(columns=['time_of_day']).isnull().mean()) * 100
    st.subheader("Процент заполненности по каналам")
    fig = px.histogram(completeness, nbins=50, labels={'value':'Заполненность (%)'})
    st.plotly_chart(fig, use_container_width=True)
    
    low_completeness = completeness[completeness < 50]
    if not low_completeness.empty:
        st.warning(f"Найдено {len(low_completeness)} каналов с заполненностью менее 50%")
        st.dataframe(low_completeness.reset_index().rename(columns={'index':'Канал', 0:'Заполненность (%)'}))
    else:
        st.success("Все каналы имеют заполненность более 50%")
    
    st.subheader("Интервалы полного отсутствия данных")
    all_missing = missing_by_time[missing_by_time == len(df.columns)-1]
    if not all_missing.empty:
        st.write("Временные метки, где все каналы отсутствуют:")
        st.write(all_missing.index.strftime('%d.%m.%Y %H:%M').tolist())
    else:
        st.write("Нет интервалов с полным отсутствием данных.")

# ==================== TAB 3: Временные ряды ====================
with tab3:
    st.header("Просмотр временных рядов")
    
    zone_filter = st.multiselect("Фильтр по зоне суток", 
                                 options=['Ночь', 'Утро', 'День', 'Вечер', 'Неопределено'],
                                 default=['Ночь', 'Утро'])
    
    selected_channels = st.multiselect("Выберите каналы для отображения", 
                                       options=[c for c in df.columns if c != 'time_of_day'],
                                       default=[c for c in df.columns[:3] if c != 'time_of_day'] if len(df.columns) > 3 else [])
    
    if selected_channels and zone_filter:
        filtered_df = df[df['time_of_day'].isin(zone_filter)]
        if filtered_df.empty:
            st.warning("Нет данных для выбранных зон суток.")
        else:
            fig = go.Figure()
            for ch in selected_channels:
                fig.add_trace(go.Bar(x=filtered_df.index, y=filtered_df[ch], name=ch[:50]))
            fig.update_layout(title="Напряжение по времени", xaxis_title="Время", yaxis_title="Напряжение, В")
            st.plotly_chart(fig, use_container_width=True)
            
            if st.checkbox("Показать среднее по выбранным каналам"):
                mean_series = filtered_df[selected_channels].mean(axis=1)
                fig2 = px.bar(x=mean_series.index, y=mean_series.values, 
                              labels={'x':'Время', 'y':'Среднее напряжение, В'})
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Выберите хотя бы один канал и зону суток.")

# ==================== TAB 4: Статистика и распределение ====================
with tab4:
    st.header("Статистический анализ")
    
    zones = df['time_of_day'].unique()
    selected_zone = st.selectbox("Выберите зону суток для детальной статистики", options=zones)
    zone_df = df[df['time_of_day'] == selected_zone].drop(columns=['time_of_day'])
    
    st.subheader(f"Статистика для зоны '{selected_zone}'")
    stats_zone = zone_df.describe().T
    st.dataframe(stats_zone[['min', 'max', 'mean', 'std']].round(1))
    
    st.subheader("Распределение напряжений (все каналы, все моменты)")
    all_values = df.drop(columns=['time_of_day']).values.flatten()
    all_values = all_values[~np.isnan(all_values)]
    fig = px.histogram(x=all_values, nbins=100, labels={'x':'Напряжение, В'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Средние напряжения по фазам (по всем зонам)")
    phase_stats = {}
    for phase in ['0','1','2','3']:
        cols = meta_df[meta_df['phase'] == phase].index
        if len(cols) > 0:
            phase_data = df[cols].values.flatten()
            phase_data = phase_data[~np.isnan(phase_data)]
            if len(phase_data) > 0:
                phase_stats[phase] = {
                    'mean': np.mean(phase_data),
                    'min': np.min(phase_data),
                    'max': np.max(phase_data)
                }
    phase_df = pd.DataFrame(phase_stats).T
    phase_df.index = ['Одна фаза' if i=='0' else f'Фаза {i}' for i in phase_df.index]
    st.dataframe(phase_df.round(1))
    
    st.subheader("Среднее напряжение по всем каналам во времени (по зонам)")
    mean_over_time = df.drop(columns=['time_of_day']).mean(axis=1, skipna=True)
    fig = px.line(x=mean_over_time.index, y=mean_over_time.values, color=df['time_of_day'],
                  labels={'x':'Время', 'y':'Среднее напряжение, В', 'color':'Зона суток'})
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: Аномалии ====================
with tab5:
    st.header("Выявление аномальных режимов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Каналы с напряжением ниже {min_alarm} В")
        low_cols = []
        for col in df.columns:
            if col == 'time_of_day':
                continue
            if df[col].min() < min_alarm:
                low_cols.append(col)
        if low_cols:
            low_data = []
            for col in low_cols:
                low_data.append({
                    'Канал': col,
                    'Населённый пункт': meta_df.loc[col, 'settlement'],
                    'Фаза': meta_df.loc[col, 'phase'],
                    'Минимум, В': df[col].min(),
                    'Время минимума': df[col].idxmin().strftime('%d.%m.%Y %H:%M')
                })
            low_df = pd.DataFrame(low_data).sort_values('Минимум, В')
            st.dataframe(low_df)
        else:
            st.success(f"Нет каналов с напряжением ниже {min_alarm} В")
    
    with col2:
        st.subheader(f"Каналы с напряжением выше {max_alarm} В")
        high_cols = []
        for col in df.columns:
            if col == 'time_of_day':
                continue
            if df[col].max() > max_alarm:
                high_cols.append(col)
        if high_cols:
            high_data = []
            for col in high_cols:
                high_data.append({
                    'Канал': col,
                    'Населённый пункт': meta_df.loc[col, 'settlement'],
                    'Фаза': meta_df.loc[col, 'phase'],
                    'Максимум, В': df[col].max(),
                    'Время максимума': df[col].idxmax().strftime('%d.%m.%Y %H:%M')
                })
            high_df = pd.DataFrame(high_data).sort_values('Максимум, В', ascending=False)
            st.dataframe(high_df)
        else:
            st.success(f"Нет каналов с напряжением выше {max_alarm} В")
    
    st.subheader(f"Несимметрия фаз (ΔU между max и min фазой > {asymmetry_threshold} В)")
    base_names = {}
    for col in df.columns:
        if col == 'time_of_day':
            continue
        base = re.sub(r', фаза \d', '', col)
        base_names[col] = base
    
    obj_to_cols = {}
    for col, base in base_names.items():
        obj_to_cols.setdefault(base, []).append(col)
    
    asymmetry_data = []
    for obj, cols in obj_to_cols.items():
        if len(cols) < 2:
            continue
        obj_df = df[cols].dropna()
        if obj_df.empty:
            continue
        obj_range = obj_df.max(axis=1) - obj_df.min(axis=1)
        max_range = obj_range.max()
        if max_range > asymmetry_threshold:
            time_max_range = obj_range.idxmax()
            asymmetry_data.append({
                'Объект': obj,
                'Количество фаз': len(cols),
                'Максимальная несимметрия, В': round(max_range, 1),
                'Время': time_max_range.strftime('%d.%m.%Y %H:%M'),
                'Зона суток': df.loc[time_max_range, 'time_of_day']
            })
    
    if asymmetry_data:
        asym_df = pd.DataFrame(asymmetry_data).sort_values('Максимальная несимметрия, В', ascending=False)
        st.dataframe(asym_df)
    else:
        st.success(f"Не обнаружено объектов с несимметрией выше {asymmetry_threshold} В")

# ==================== TAB 6: Корреляционный анализ ====================
with tab6:
    st.header("Корреляционный анализ")
    
    st.markdown(f"**Метод:** {corr_method.upper()}, порог отображения: |r| > {corr_threshold}")
    
    zone_corr = st.multiselect("Выберите зоны суток для корреляции", 
                               options=['Ночь', 'Утро', 'День', 'Вечер', 'Неопределено'],
                               default=['Ночь', 'Утро', 'День', 'Вечер'])
    
    if not zone_corr:
        st.warning("Выберите хотя бы одну зону суток.")
    else:
        corr_df = df[df['time_of_day'].isin(zone_corr)].drop(columns=['time_of_day'])
        if corr_df.empty:
            st.warning("Нет данных для выбранных зон.")
        else:
            all_channels = [c for c in corr_df.columns]
            selected_corr_channels = st.multiselect("Выберите каналы для расчёта корреляции (оставьте пустым - все каналы)", 
                                                     options=all_channels)
            if not selected_corr_channels:
                selected_corr_channels = all_channels
            
            if len(selected_corr_channels) < 2:
                st.warning("Выберите не менее двух каналов.")
            else:
                # Корреляционная матрица
                corr_matrix = corr_df[selected_corr_channels].corr(method=corr_method)
                
                # Тепловая карта
                fig = px.imshow(corr_matrix,
                                text_auto=True,
                                aspect="auto",
                                color_continuous_scale='RdBu_r',
                                zmin=-1, zmax=1,
                                title=f"Корреляционная матрица ({corr_method.upper()})")
                fig.update_layout(width=800, height=700)
                st.plotly_chart(fig, use_container_width=True)
                
                # Таблица сильных корреляций
                st.subheader("Наиболее сильные корреляции")
                corr_unstacked = corr_matrix.unstack().reset_index()
                corr_unstacked.columns = ['Канал 1', 'Канал 2', 'Корреляция']
                corr_unstacked = corr_unstacked[corr_unstacked['Канал 1'] != corr_unstacked['Канал 2']]
                corr_unstacked['abs'] = np.abs(corr_unstacked['Корреляция'])
                corr_unstacked = corr_unstacked.drop_duplicates(subset=['abs'], keep='first').sort_values('abs', ascending=False)
                strong_corr = corr_unstacked[corr_unstacked['abs'] > corr_threshold].head(20)
                st.dataframe(strong_corr[['Канал 1', 'Канал 2', 'Корреляция']].round(3))
                
                # Корреляция по каждой зоне отдельно
                st.subheader("Корреляция по каждой зоне суток")
                for zone in zone_corr:
                    zone_data = df[df['time_of_day'] == zone][selected_corr_channels].dropna()
                    if len(zone_data) < 2:
                        st.write(f"В зоне '{zone}' недостаточно данных.")
                        continue
                    zone_corr_matrix = zone_data.corr(method=corr_method)
                    st.write(f"**Зона: {zone}**")
                    z_unstacked = zone_corr_matrix.unstack().reset_index()
                    z_unstacked.columns = ['Канал 1', 'Канал 2', 'Корреляция']
                    z_unstacked = z_unstacked[z_unstacked['Канал 1'] != z_unstacked['Канал 2']]
                    z_unstacked['abs'] = np.abs(z_unstacked['Корреляция'])
                    z_unstacked = z_unstacked.drop_duplicates(subset=['abs'], keep='first').sort_values('abs', ascending=False)
                    z_strong = z_unstacked[z_unstacked['abs'] > corr_threshold].head(10)
                    if not z_strong.empty:
                        st.dataframe(z_strong[['Канал 1', 'Канал 2', 'Корреляция']].round(3))
                    else:
                        st.write("Нет значимых корреляций.")
                
                # ------------------ ГРУППИРОВКА КАНАЛОВ ПО КОРРЕЛЯЦИИ ------------------
                st.subheader("Группировка каналов по высокой корреляции")
                st.markdown(f"Каналы считаются связанными, если коэффициент корреляции > **{cluster_threshold}**. Группы формируются как связные компоненты графа.")
                
                # Обработка возможных NaN в корреляционной матрице
                if corr_matrix.isnull().any().any():
                    st.warning("В корреляционной матрице есть NaN. Они заменены на 0 (нет корреляции).")
                    corr_matrix = corr_matrix.fillna(0)
                
                # Преобразуем в numpy массив для работы с графами
                adj_np = (np.abs(corr_matrix.values) > cluster_threshold).astype(int)
                np.fill_diagonal(adj_np, 0)  # убираем связь канала с самим собой
                
                # Поиск связных компонент
                n_components, labels = connected_components(adj_np, directed=False)
                
                # Собираем группы
                groups = {}
                for i, ch in enumerate(selected_corr_channels):
                    comp = labels[i]
                    groups.setdefault(comp, []).append(ch)
                
                # Подготовка данных для итоговой таблицы групп (в длинном формате)
                group_long_records = []
                for comp, ch_list in groups.items():
                    if len(ch_list) >= 2:
                        # Рассчитываем среднюю абсолютную корреляцию внутри группы
                        sub_corr = corr_matrix.loc[ch_list, ch_list]
                        mask = np.ones(sub_corr.shape, dtype=bool)
                        np.fill_diagonal(mask, 0)
                        avg_corr = np.abs(sub_corr.values[mask]).mean() if mask.sum() > 0 else 0
                        for ch in ch_list:
                            group_long_records.append({
                                'Группа': comp + 1,
                                'Размер группы': len(ch_list),
                                'Канал': ch,
                                'Населённый пункт': meta_df.loc[ch, 'settlement'],
                                'Фаза': meta_df.loc[ch, 'phase'],
                                'Средняя |корреляция| внутри группы': round(avg_corr, 3)
                            })
                
                if group_long_records:
                    groups_long_df = pd.DataFrame(group_long_records).sort_values(['Группа', 'Канал'])
                    
                    # Кнопка скачивания Excel (длинный формат)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        groups_long_df.to_excel(writer, index=False, sheet_name='Каналы в группах')
                    output.seek(0)
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.download_button(
                            label="📥 Скачать список каналов по группам (Excel)",
                            data=output,
                            file_name=f"группы_каналов_детально_{cluster_threshold}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    with col2:
                        n_groups = len(groups_long_df['Группа'].unique())
                        st.write(f"Найдено **{n_groups}** групп размером >= 2, всего **{len(groups_long_df)}** каналов в группах.")
                    
                    # Отображаем сводную таблицу групп (для быстрого просмотра)
                    st.subheader("Сводная таблица групп")
                    summary_records = []
                    for comp, ch_list in groups.items():
                        if len(ch_list) >= 2:
                            settlements = [meta_df.loc[ch, 'settlement'] for ch in ch_list]
                            phases = [meta_df.loc[ch, 'phase'] for ch in ch_list]
                            sub_corr = corr_matrix.loc[ch_list, ch_list]
                            mask = np.ones(sub_corr.shape, dtype=bool)
                            np.fill_diagonal(mask, 0)
                            avg_corr = np.abs(sub_corr.values[mask]).mean() if mask.sum() > 0 else 0
                            summary_records.append({
                                'Группа': comp + 1,
                                'Размер': len(ch_list),
                                'Населённые пункты': ', '.join(set(settlements)),
                                'Фазы': ', '.join(sorted(set(phases))),
                                'Средняя |корреляция|': round(avg_corr, 3)
                            })
                    summary_df = pd.DataFrame(summary_records).sort_values('Размер', ascending=False)
                    st.dataframe(summary_df)
                    
                    # Отображение деталей каждой группы в expander
                    for comp, ch_list in groups.items():
                        if len(ch_list) >= 2:
                            with st.expander(f"**Группа {comp+1}** (размер {len(ch_list)}), порог {cluster_threshold}"):
                                group_info = []
                                for ch in ch_list:
                                    group_info.append({
                                        'Канал': ch,
                                        'Нас. пункт': meta_df.loc[ch, 'settlement'],
                                        'Фаза': meta_df.loc[ch, 'phase']
                                    })
                                st.dataframe(pd.DataFrame(group_info))
                                
                                if st.checkbox(f"Показать временные ряды для группы {comp+1}", key=f"plot_group_{comp}"):
                                    plot_df = df[df['time_of_day'].isin(zone_corr)][ch_list]
                                    if plot_df.empty:
                                        st.warning("Нет данных для построения графиков.")
                                    else:
                                        fig = go.Figure()
                                        for ch in ch_list:
                                            fig.add_trace(go.Bar(x=filtered_df.index, y=filtered_df[ch], name=ch[:50]))
                                        fig.update_layout(title=f"Временные ряды группы {comp+1}", xaxis_title="Время", yaxis_title="Напряжение, В")
                                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Нет групп с размером >= 2. Попробуйте уменьшить порог.")

# ==================== TAB 7: Рекомендации ====================
with tab7:
    st.header("Рекомендации по результатам анализа")
    
    st.markdown("""
    На основе выявленных аномалий сформированы следующие рекомендации:
    """)
    
    low_alarm_list = []
    for col in df.columns:
        if col == 'time_of_day':
            continue
        if df[col].min() < min_alarm:
            low_alarm_list.append({
                'Канал': col,
                'Нас. пункт': meta_df.loc[col, 'settlement'],
                'Мин. напряжение': df[col].min()
            })
    
    high_alarm_list = []
    for col in df.columns:
        if col == 'time_of_day':
            continue
        if df[col].max() > max_alarm:
            high_alarm_list.append({
                'Канал': col,
                'Нас. пункт': meta_df.loc[col, 'settlement'],
                'Макс. напряжение': df[col].max()
            })
    
    if low_alarm_list:
        st.warning("#### 1. Объекты с пониженным напряжением")
        st.write("Следующие каналы требуют проверки технического состояния (возможны перегрузка, плохой контакт, недостаточная мощность трансформатора):")
        low_df_rec = pd.DataFrame(low_alarm_list).sort_values('Мин. напряжение')
        st.dataframe(low_df_rec)
    else:
        st.success("#### 1. Объекты с пониженным напряжением не обнаружены")
    
    if high_alarm_list:
        st.warning("#### 2. Объекты с повышенным напряжением")
        st.write("Следующие каналы имели кратковременные превышения. Рекомендуется проверить работу регуляторов напряжения и устройств защиты:")
        high_df_rec = pd.DataFrame(high_alarm_list).sort_values('Макс. напряжение', ascending=False)
        st.dataframe(high_df_rec)
    else:
        st.success("#### 2. Объекты с повышенным напряжением не обнаружены")
    
    # Несимметрия
    asymmetry_data_rec = []
    base_names = {}
    for col in df.columns:
        if col == 'time_of_day':
            continue
        base = re.sub(r', фаза \d', '', col)
        base_names[col] = base
    obj_to_cols = {}
    for col, base in base_names.items():
        obj_to_cols.setdefault(base, []).append(col)
    for obj, cols in obj_to_cols.items():
        if len(cols) < 2:
            continue
        obj_df = df[cols].dropna()
        if obj_df.empty:
            continue
        obj_range = obj_df.max(axis=1) - obj_df.min(axis=1)
        max_range = obj_range.max()
        if max_range > asymmetry_threshold:
            asymmetry_data_rec.append({
                'Объект': obj,
                'Макс. несимметрия, В': round(max_range, 1)
            })
    if asymmetry_data_rec:
        st.warning("#### 3. Несимметрия фаз")
        st.write("Обнаружена значительная несимметрия по фазам. Рекомендуется выполнить замеры нагрузки и при необходимости перераспределить нагрузку:")
        asym_df_rec = pd.DataFrame(asymmetry_data_rec).sort_values('Макс. несимметрия, В', ascending=False)
        st.dataframe(asym_df_rec)
    else:
        st.success("#### 3. Несимметрия фаз в пределах нормы")
    
    completeness = (1 - df.drop(columns=['time_of_day']).isnull().mean()) * 100
    bad_channels = completeness[completeness < 50].index.tolist()
    if bad_channels:
        st.warning("#### 4. Каналы с низкой заполненностью")
        st.write("Следующие каналы имеют менее 50% заполненных данных. Рекомендуется проверить работу приборов учёта и систему сбора данных:")
        st.write(bad_channels)
    else:
        st.success("#### 4. Все каналы имеют достаточную заполненность данных")
    
    # --- Кнопка выгрузки итоговой таблицы аномалий ---
    st.subheader("📥 Выгрузка итоговой таблицы аномалий")
    
    # Собираем все аномалии в один DataFrame (по каналам)
    anomaly_records = []
    
    # Низкое напряжение
    for col in low_alarm_list:
        anomaly_records.append({
            'Тип аномалии': 'Напряжение ниже порога',
            'Канал': col['Канал'],
            'Населённый пункт': col['Нас. пункт'],
            'Фаза': meta_df.loc[col['Канал'], 'phase'],
            'Значение, В': col['Мин. напряжение'],
            'Время': df[col['Канал']].idxmin().strftime('%d.%m.%Y %H:%M') if pd.notna(df[col['Канал']].idxmin()) else '',
            'Зона суток': df.loc[df[col['Канал']].idxmin(), 'time_of_day'] if pd.notna(df[col['Канал']].idxmin()) else ''
        })
    
    # Высокое напряжение
    for col in high_alarm_list:
        anomaly_records.append({
            'Тип аномалии': 'Напряжение выше порога',
            'Канал': col['Канал'],
            'Населённый пункт': col['Нас. пункт'],
            'Фаза': meta_df.loc[col['Канал'], 'phase'],
            'Значение, В': col['Макс. напряжение'],
            'Время': df[col['Канал']].idxmax().strftime('%d.%m.%Y %H:%M') if pd.notna(df[col['Канал']].idxmax()) else '',
            'Зона суток': df.loc[df[col['Канал']].idxmax(), 'time_of_day'] if pd.notna(df[col['Канал']].idxmax()) else ''
        })
    
    # Несимметрия (добавляем все каналы объекта, где обнаружена несимметрия)
    if asymmetry_data_rec:
        # нужно связать объект и каналы
        for obj_rec in asymmetry_data_rec:
            obj_name = obj_rec['Объект']
            # найдём все каналы, соответствующие этому объекту
            obj_channels = [col for col, base in base_names.items() if base == obj_name]
            for ch in obj_channels:
                anomaly_records.append({
                    'Тип аномалии': 'Несимметрия фаз',
                    'Канал': ch,
                    'Населённый пункт': meta_df.loc[ch, 'settlement'],
                    'Фаза': meta_df.loc[ch, 'phase'],
                    'Значение, В': obj_rec['Макс. несимметрия, В'],
                    'Время': '',  # можно добавить время максимума несимметрии, но оно уже не привязано к каналу
                    'Зона суток': ''
                })
    
    if anomaly_records:
        anomaly_df = pd.DataFrame(anomaly_records).sort_values(['Тип аномалии', 'Значение, В'], ascending=[True, False])
        
        output_anomaly = io.BytesIO()
        with pd.ExcelWriter(output_anomaly, engine='openpyxl') as writer:
            anomaly_df.to_excel(writer, index=False, sheet_name='Аномалии')
        output_anomaly.seek(0)
        
        st.download_button(
            label="📥 Скачать итоговую таблицу аномалий (Excel)",
            data=output_anomaly,
            file_name="аномалии_напряжения.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Аномалий не обнаружено.")
    
    st.info("""
    **Общее заключение:**  
    Качество напряжения в целом удовлетворительное, однако выявлены локальные зоны с отклонениями, требующие внимания.
    Рекомендуется провести дополнительные инструментальные проверки в указанных точках и принять меры по нормализации режимов работы сети.
    """)

st.markdown("---")
#st.caption("Приложение для анализа 10-минутных срезов напряжения. Разработано на основе файла-шаблона.")
