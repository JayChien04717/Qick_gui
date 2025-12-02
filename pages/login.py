from nicegui import ui, app


USERS = [
    {'account': 'SQC', 
    'password': 'test'
    },
]

def add_page(app_state):
    @ui.page('/login')
    def login_page():
        def try_login():

            user = next((u for u in USERS if u['account'] == username.value), None)

            if user and user['password'] == password.value:
                app.storage.user['authenticated'] = True
                ui.navigate.to('/')
            else:
                ui.notify('Wrong username or password', color='negative')

        with ui.card().classes('absolute-center w-80 p-6 items-center'):
            ui.label('Lab GUI Login').classes('text-xl font-bold mb-4')
            username = ui.input('Username').on('keydown.enter', try_login).classes('w-full')
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login).classes('w-full')
            ui.button('Log in', on_click=try_login).classes('w-full mt-4')

