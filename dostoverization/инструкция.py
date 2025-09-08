import streamlit as st

# st.components.v1.html(
# """ <iframe frameborder="5" src="https://datalens.yandex/ctuxlru5a0jky?_no_controls=5"></iframe>"""
# )

st.text('инструкция')

# Используем iFrame для показа PDF
st.write(f'<iframe src="dostoverization/merkuriy-255-avlg-811-01-00-ps-2021-06-02.pdf" width="200%" height="1600px"></iframe>', unsafe_allow_html=True)
