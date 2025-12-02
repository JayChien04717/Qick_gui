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
    if not app.storage.user.get('authenticated', False):
        return ui.navigate.to('/login')

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

        # ------------------------------
        # 中間：目前選到的 page 內容（可捲動）
        # ------------------------------
        with ui.column().classes("flex-1 h-full p-6 gap-4 overflow-y-auto bg-white"):
            # 你如果還是想要中間上面有標題，可以加一行：
            # ui.label('Quantum Lab GUI').classes('text-2xl font-bold')
            # ui.separator()

            with ui.column().classes("gap-4"):
                content_fn()

        # ------------------------------
        # 右側：Experiment Config 欄（你原本的 sidebar）
        # ------------------------------
        experiment_config_sidebar(app_state)
