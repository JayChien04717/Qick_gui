from nicegui import ui, app

# Simple user database
# 格式為 { '帳號': '密碼' }
USERS = {
    'SQC': 'test',  # 這裡設定：帳號是 SQC，密碼是 test
}

def add_page(app_state):
    @ui.page('/login')
    def login_page():
        def try_login():
            # USERS.get(帳號輸入框的值) 會去尋找對應的密碼
            # 如果找到的密碼 == 密碼輸入框的值，則登入成功
            if USERS.get(username.value) == password.value:
                app.storage.user['authenticated'] = True
                ui.navigate.to('/')
            else:
                ui.notify('Wrong username or password', color='negative')

        with ui.card().classes('absolute-center w-80 p-6 items-center'):
            ui.label('Lab GUI Login').classes('text-xl font-bold mb-4')
            username = ui.input('Username').on('keydown.enter', try_login).classes('w-full')
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login).classes('w-full')
            ui.button('Log in', on_click=try_login).classes('w-full mt-4')