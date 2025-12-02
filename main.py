from nicegui import ui, app
from pyngrok import ngrok
import Pyro4
from state.app_state import AppState
# 引入頁面
from pages import connect, onetone, twotone, prabi, ramsey, spinecho, t1, singleshot, login

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION = 4

def init_ngrok():
    ngrok.set_auth_token("36GmTaQXU6v3oYZuKgv5v3hA0F4_WJQB2kESnnwQkfYQzrtG")
    ngrok.kill()
    tunnel = ngrok.connect(8081, bind_tls=True)
    print(f"\n==============================================")
    print(f" 🌍 Ngrok URL: {tunnel.public_url}")
    print(f"==============================================\n")

def main():
    app_state = AppState()
    login.add_page(app_state)
    connect.add_page(app_state)
    onetone.add_page(app_state)
    twotone.add_page(app_state)
    prabi.add_page(app_state)
    ramsey.add_page(app_state)
    spinecho.add_page(app_state)
    t1.add_page(app_state)
    singleshot.add_page(app_state)
    
    app.on_startup(init_ngrok)

if __name__ in {"__main__", "__mp_main__"}:
    main()
    ui.run(title="Lab GUI", reload=True, port=8081, storage_secret='secure_lab_key_12345')