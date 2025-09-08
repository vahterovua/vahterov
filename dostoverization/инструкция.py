import streamlit as st

# st.components.v1.html(
# """ <iframe frameborder="5" src="https://datalens.yandex/ctuxlru5a0jky?_no_controls=5"></iframe>"""
# )

st.text('инструкция')

# Создадим поле выбора для даты
show_timerange = st.sidebar.checkbox("Show date range")
if show_timerange == True:
    # Вычислим даты для создания временного слайдера
    min_ts = min(df[DATE_COLUMN]).to_pydatetime()
    max_ts = max(df[DATE_COLUMN]).to_pydatetime()
    day_date = pd.to_datetime(st.sidebar.slider("Date to chose", min_value=min_ts, max_value=max_ts, value=max_ts))
    st.write(f"Data for {day_date.date()}")
    df = df[(df['date'] == day_date)]

# Создадим поле выбора для визуализации общего количества случаев, смертей или вакцинаций
select_event = st.sidebar.selectbox('Show map', ('cases per million', 'deaths per million', 'vaccinated per hundred'))
if select_event == 'cases per million':
    st.plotly_chart(draw_map_cases(), use_container_width=True)

if select_event == 'deaths per million':
    st.plotly_chart(draw_map_deaths(), use_container_width=True)

if select_event == 'vaccinated per hundred':
    st.plotly_chart(draw_map_vaccine(), use_container_width=True)



