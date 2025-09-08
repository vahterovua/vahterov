import streamlit as st

# st.components.v1.html(
# """ <iframe frameborder="5" src="https://datalens.yandex/ctuxlru5a0jky?_no_controls=5"></iframe>"""
# )

st.text('инструкция')

# Используем iFrame для показа PDF
st.write(f'<iframe src="https://www.incotexcom.ru/files/em/certificate/merkuriy-230-sertifikat-26-b-04143-24-mossar-do-2027-06-09.pdf" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
