import streamlit as st

st.title("Достоверизация")

# Инициализация состояния сеанса
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    
if "dir_name" not in st.session_state:
    st.session_state.dir_name = ""

# Логика авторизации
def login():
    # Поле для ввода логина
    dir_name = st.text_input("Введите свой логин и нажмите Enter:", value="")
    if dir_name:
        st.session_state.dir_name = dir_name
        st.session_state.logged_in = True
        st.rerun()

# Страница авторизации
login_page = st.Page(login, title="Log in")

# Другие страницы приложения
file_show = st.Page("Просмотр-файлов.py", title="Просмотр файлов", default=False)
file_processing = st.Page("Достоверизация.py", title="Достоверизация", default=True)
show_graph = st.Page("Просмотр-графиков.py", title="Просмотр графиков", default=False)
file_processing_1tu = st.Page("Достоверизация-1ТУ.py", title="Достоверизация по одной точке,2 варианта ", default=False)
new_processing = st.Page("new_достоверизация.py", title="new_достоверизация", default=False)
new_graf = st.Page("new_Просмотр-графиков.py", title="new_Просмотр-графиков", default=False)
instr = st.Page("инструкция.py", title="инструкция", default=False)

# Основная логика приложения
if st.session_state.logged_in:
    # Создание боковых панелей и навигации
    pg = st.navigation({
        " ": [file_processing, show_graph, file_processing_1tu, file_show,new_processing,new_graf,instr]
    })
    # Показываем имя пользователя в боковой панели
    st.sidebar.markdown(f"Папка : {st.session_state.dir_name}")
    
    # Кнопка выхода из системы
    if st.sidebar.button("Log out", key="logout_button"):  # Убрали аргумент 'icon'
        st.session_state.logged_in = False
        st.session_state.dir_name = ""
        st.rerun()
        
else:
    # Пока пользователь не залогинился, выводится только страница авторизации
    pg = st.navigation([login_page])

# Запуск выбранной страницы
pg.run()