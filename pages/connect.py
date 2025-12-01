# pages/connect.py
from nicegui import ui
from layout.layout import page_layout

from qick.pyro import make_proxy
import asyncio


def add_page(app_state):
    @ui.page("/")
    def connect_page():
        def content():
            # ============================================================
            # 🔵 左右排列：左邊 Connect，右邊 SOCCFG
            # ============================================================
            with ui.row().classes("w-full gap-6 items-start"):
                # --------------------------------------------------------
                # ⬅ 左邊：Connect Instrument
                # --------------------------------------------------------
                with ui.column().classes("max-w-md"):
                    ui.label("Connect Instrument").classes("text-xl font-semibold")

                    with ui.card().classes("w-full p-4"):
                        ui.label("Instrument Settings").classes("font-semibold")

                        ui.input("Namespace IP").bind_value(app_state, "instrument_ip")
                        ui.number("Namespace Port", format="%d").bind_value(
                            app_state, "instrument_port"
                        )
                        ui.input("Proxy Name").bind_value(app_state, "proxy_name")

                        async def do_connect():
                            ui.notify("Connecting...", type="info")
                            try:
                                # Use asyncio.to_thread for blocking connection
                                soc, soccfg = await asyncio.to_thread(
                                    make_proxy,
                                    ns_host=app_state.instrument_ip,
                                    ns_port=app_state.instrument_port,
                                    proxy_name=app_state.proxy_name,
                                )
                                app_state.soc = soc
                                app_state.soccfg = soccfg
                                app_state.instrument_connected = True

                                ui.notify("Connected to QICK!", type="positive")
                                soccfg_view.refresh()

                            except Exception as e:
                                app_state.instrument_connected = False
                                ui.notify(f"Connection failed: {e}", type="negative")
                                soccfg_view.refresh()

                        async def do_disconnect():
                            app_state.soc = None
                            app_state.soccfg = None
                            app_state.instrument_connected = False
                            ui.notify("Disconnected.", type="info")
                            soccfg_view.refresh()

                        with ui.row().classes("w-full gap-2"):
                            ui.button("Connect", on_click=do_connect, color="green").bind_enabled_from(
                                app_state, "instrument_connected", backward=lambda x: not x
                            )
                            ui.button("Disconnect", on_click=do_disconnect, color="red").bind_enabled_from(
                                app_state, "instrument_connected"
                            )

                        ui.label().bind_text_from(
                            app_state,
                            "instrument_connected",
                            lambda v: "Status: CONNECTED ✅"
                            if v
                            else "Status: DISCONNECTED ❌",
                        )

                # --------------------------------------------------------
                # ➡ 右邊：SOCCFG 顯示
                # --------------------------------------------------------
                with ui.column().classes("flex-1 min-w-[500px]"):

                    @ui.refreshable
                    def soccfg_view():
                        ui.label("QICK SoC Config").classes("text-xl font-semibold mb-2")

                        if app_state.soccfg is None:
                            ui.label("No SoC Config loaded. Please connect first.").classes(
                                "text-gray-500"
                            )
                            return

                        # 大型可捲動 code 顯示區塊
                        with ui.card().classes("w-full h-[800px] overflow-y-auto p-4"):
                            ui.code(str(app_state.soccfg)).classes(
                                "text-sm whitespace-pre-wrap"
                            )

                    soccfg_view()

        page_layout(app_state, content)
