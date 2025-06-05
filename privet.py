import streamlit as st
st.text('привет')
st.text('приветики')

url = 'https://storage.googleapis.com/s4a-prod-share-preview/default/default_github_user_logo.png' # ссылка на картинку
st.image(url, caption='Картинка по ссылке')
