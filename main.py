from nicegui import ui, app
from pyngrok import ngrok
import Pyro4
from state.app_state import AppState
# 引入頁面
from pages import connect, onetone, twotone, prabi, ramsey, spinecho, t1, singleshot, login

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION = 4

def init_ngrok():
    # TODO: Replace with your actual token
    # 注意：將 token 寫在程式碼中有外洩風險，請小心保管
    ngrok.set_auth_token("ngrok token")
    
    # Kill existing tunnels to avoid conflicts
    ngrok.kill()
    
    tunnel = ngrok.connect(8081, bind_tls=True)
    print(f"\n==============================================")
    print(f" 🌍 Ngrok URL: {tunnel.public_url}")
    print(f"==============================================\n")

def main():

    app_state = AppState()

    # 註冊頁面
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
    # ==========================================
    # 🔐 4. 重要：啟用 storage_secret
    # ==========================================
    # 為了讓 app.storage.user 能運作，必須設定 storage_secret
    # 請隨便打一串亂碼當作密鑰
    ui.run(title="Lab GUI", reload=True, port=8081, storage_secret='secure_lab_key_12345')