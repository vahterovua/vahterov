import numpy as np
import pandas as pd
import streamlit as st
from datetime import timedelta
from statsmodels.tsa.arima.model import ARIMA
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

# Генерация исходных данных
start_date = '2023-01-01'
end_date = '2023-02-28'
index = pd.date_range(start=start_date, end=end_date)

num_devices = 5
active_energy = np.random.uniform(low=50, high=200, size=(len(index), num_devices))
reactive_energy = np.random.uniform(low=10, high=50, size=(len(index), num_devices))

df = pd.DataFrame(data=np.column_stack((active_energy.flatten(), reactive_energy.flatten())),
                  columns=['ActiveEnergy', 'ReactiveEnergy'])
df['DeviceID'] = np.repeat(np.arange(num_devices), len(index))
df['Date'] = np.tile(index, num_devices)

# Добавление некоторых аномальных значений
anomalies_idx = np.random.choice(df.index, size=int(len(df)*0.05), replace=False)
df.loc[anomalies_idx, ['ActiveEnergy']] *= 3

# Настройка интерфейса Streamlit
st.title('Анализ потребления электроэнергии')

# Выбор устройства
devices = st.multiselect('Выберите устройство:', list(range(num_devices)))

# Выбираем диапазон дат
start_date = st.date_input('Начальная дата:', index.min().to_pydatetime().date())
end_date = st.date_input('Конечная дата:', index.max().to_pydatetime().date())

# Фильтруем данные по выбранному устройству и диапазону дат
if devices:
    filtered_df = df[(df['DeviceID'].isin(devices)) &
                     ((df['Date'] >= str(start_date)) & (df['Date'] <= str(end_date)))]
else:
    filtered_df = df.copy()

# Отображение графиков
if not filtered_df.empty:
    active_fig = px.line(filtered_df, x='Date', y='ActiveEnergy', color='DeviceID', title='Активная энергия')
    reactive_fig = px.line(filtered_df, x='Date', y='ReactiveEnergy', color='DeviceID', title='Реактивная энергия')

    st.plotly_chart(active_fig)
    st.plotly_chart(reactive_fig)

# Скачивание данных
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

csv = convert_df_to_csv(filtered_df)
st.download_button(label="Скачать CSV-файл",
                   data=csv,
                   file_name='energy_data.csv',
                   mime='text/csv')

# Обнаружение аномалий
threshold = st.slider('Отступ отклонения аномалии (%)', min_value=0, max_value=100, value=20)

if threshold > 0:
    threshold_value = threshold / 100
    anomaly_indices = []
    for col in ['ActiveEnergy']:
        mean_col = df[col].mean()
        std_col = df[col].std()

        upper_bound = mean_col + threshold_value * std_col
        lower_bound = mean_col - threshold_value * std_col

        anomalies = df[(df[col] > upper_bound) | (df[col] < lower_bound)]
        anomaly_indices.extend(anomalies.index.tolist())

    if len(anomaly_indices) > 0:
        st.write(f'Обнаружено {len(anomaly_indices)} аномальных значений.')
    else:
        st.write('Нет обнаруженных аномалий.')

# Прогнозирование потребления
if st.button('Прогноз'):
    device_id = st.selectbox('Выберите устройство для прогнозирования:', list(range(num_devices)), key='forecast_device')
    selected_device = df[df['DeviceID'] == device_id]
    model = ARIMA(selected_device['ActiveEnergy'], order=(1,1,1)).fit()
    forecast = model.forecast(steps=10)

    fig = px.line(x=selected_device['Date'], y=selected_device['ActiveEnergy'], labels={'y':'Active Energy'}, title=f'Прогноз потребления для устройства {device_id}')
    fig.add_scatter(x=pd.date_range(end=end_date, periods=10)[1:], y=forecast, mode='lines+markers', name='Forecast')
    st.plotly_chart(fig)