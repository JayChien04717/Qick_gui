from nicegui import ui, app
from typing import Callable, Any
from .sidebar import experiment_config_sidebar

# Navigation items: (Label, Path)
NAV_ITEMS = [
    ("Connect", "/"),
    ("One tone", "/onetone"),
    ("Two tone", "/twotone"),
    ('Power Rabi', '/prabi'),
    ('Ramsey', '/ramsey'),
    ('Spin Echo', '/spinecho'),
    ('T1', '/t1'),
    ('Single Shot', '/singleshot'),
    # ('QPT', '/qpt'),
]


def page_layout(app_state: Any, content_fn: Callable):
    # Auth Check
    print(f"Checking auth: {app.storage.user}")
    if not app.storage.user.get('authenticated', False):
        print("Not authenticated, redirecting to /login")
        ui.navigate.to('/login')
        return

    with ui.row().classes("w-full h-screen no-wrap bg-gray-50"):
        # ------------------------------
        # 左側：實驗 Page 選單欄（很多 page 放這裡）
        # ------------------------------
        with ui.column().classes(
            "w-64 h-full bg-slate-100 p-4 gap-3 border-r border-slate-300 overflow-y-auto"
        ):
            ui.label("Experiments").classes("text-lg font-bold")

            for label, path in NAV_ITEMS:
                ui.button(
                    label.upper(), on_click=lambda p=path: ui.navigate.to(p)
                ).classes("w-full")

            ui.separator()
            
            def logout():
                app.storage.user['authenticated'] = False
                ui.navigate.to('/login')
                
            ui.button("LOGOUT", on_click=logout, color="red").classes("w-full mt-auto")

        # ------------------------------
        # 中間：目前選到的 page 內容（可捲動）
        # ------------------------------
        with ui.column().classes("flex-1 h-full p-6 gap-4 overflow-y-auto bg-white"):
            with ui.column().classes("gap-4"):
                content_fn()

        # ------------------------------
        # 右側：Experiment Config 欄
        # ------------------------------
        experiment_config_sidebar(app_state)
