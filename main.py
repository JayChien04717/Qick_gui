print("Importing modules...")
from nicegui import ui
import Pyro4


from state.app_state import AppState
from pages import connect, onetone, twotone, prabi, ramsey, spinecho, t1, singleshot

print("Configuring Pyro4...")
# Configure Pyro4
Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.PICKLE_PROTOCOL_VERSION = 4

def main():
    print("Initializing AppState...")
    # Initialize AppState
    app_state = AppState()

    print("Adding pages...")
    # Register Pages
    connect.add_page(app_state)
    onetone.add_page(app_state)
    twotone.add_page(app_state)
    prabi.add_page(app_state)
    ramsey.add_page(app_state)
    spinecho.add_page(app_state)
    t1.add_page(app_state)
    singleshot.add_page(app_state)

print("Starting UI...")
main()
ui.run(title="Lab GUI", reload=True, port=8081)
