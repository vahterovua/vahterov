import streamlit as st
st.text('привет')
st.text('приветики')

url = 'https://avatars.mds.yandex.net/get-mpic/4881627/2a000001928b130814167dac8b895f6dbb17/optimize' # ссылка на картинку
st.image(url, caption='счетчик')

st.image('https://avatars.mds.yandex.net/get-mpic/5284145/2a000001928b13081654a0a52d587a421cb6/optimize')




import streamlit.components.v1 as components

html_code = """ <iframe frameborder="0" src="https://datalens.yandex/4hvj54abmk68q?_no_controls=1&_theme=dark"></iframe> """

components.html(html_code, height=500)

html_code = """ <iframe frameborder="0" src="https://datalens.yandex/4hvj54abmk68q?_no_controls=1&_theme=dark"></iframe>"""

components.html(html_code, width=1000, height=300, scrolling=False)

a=pip list
st.text(a)
