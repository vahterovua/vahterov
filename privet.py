import streamlit as st
st.text('привет')
st.text('приветики')

url = 'https://avatars.mds.yandex.net/get-mpic/4881627/2a000001928b130814167dac8b895f6dbb17/optimize' # ссылка на картинку
st.image(url, caption='Картинка по ссылке')
