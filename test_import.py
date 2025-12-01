import sys
import os
sys.path.append(os.getcwd())

try:
    print("Importing nicegui...")
    from nicegui import ui
    print("Importing Pyro4...")
    import Pyro4
    print("Importing AppState...")
    from state.app_state import AppState
    print("Importing pages...")
    from pages import connect, onetone, twotone
    print("Initializing AppState...")
    app_state = AppState()
    print("Adding pages...")
    connect.add_page(app_state)
    onetone.add_page(app_state)
    twotone.add_page(app_state)
    print("All checks passed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
