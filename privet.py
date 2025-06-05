import streamlit as st
st.text('привет')
st.text('приветики')

url = 'https://avatars.mds.yandex.net/get-mpic/4881627/2a000001928b130814167dac8b895f6dbb17/optimize' # ссылка на картинку
st.image(url, caption='счетчик')

st.image('https://avatars.mds.yandex.net/get-mpic/5284145/2a000001928b13081654a0a52d587a421cb6/optimize')




import streamlit.components.v1 as components

html_code = """ <iframe frameborder="0" src="https://datalens.yandex/4hvj54abmk68q?_no_controls=1&_theme=dark"></iframe> """

components.html(html_code, height=500)

html_code = """ <!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <title>Пример встраивания HTML</title> <style> body { background-color: lightblue; font-family: Arial, sans-serif; } h1 { color: navy; } </style> </head> <body> <h1>HTML + CSS в Streamlit</h1> <p>Этот текст демонстрирует возможности встраивания HTML+CSS.</p> </body> </html> """

components.html(html_code, width=None, height=300, scrolling=False)
