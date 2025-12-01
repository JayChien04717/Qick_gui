from nicegui import ui
import asyncio


def experiment_config_sidebar(app_state):
    with ui.column().classes(
        "w-72 h-full bg-slate-100 p-4 gap-4 border-l border-slate-300 overflow-y-auto"
    ):
        # Qubit Selector（附 Change）
        ui.label("Experiment Config").classes("text-lg font-bold")

        with ui.row().classes("items-center gap-2"):
            ui.select(
                options=app_state.qubit_names,
                value=app_state.selected_qubit,
            ).bind_value(app_state, "selected_qubit")

            async def apply_qubit():
                name = app_state.selected_qubit
                ui.notify(f"Loading config for {name}...", type="info")
                try:
                    # Async load to prevent blocking
                    cfg = await asyncio.to_thread(app_state.read_config, name)
                    app_state.view_cfg = cfg
                    config_view.refresh()
                    ui.notify(f"Loaded config for {name}", type="positive")
                except Exception as e:
                    ui.notify(f"Failed to load config: {e}", type="negative")

            ui.button("Change", on_click=apply_qubit, color="primary")

        ui.separator()

        # ---- refreshable config view ----
        @ui.refreshable
        def config_view():
            cfg = app_state.view_cfg
            if cfg is None:
                ui.label("No config loaded")
                return

            def update_config(key, value, prefix=""):
                """Updates the global configuration when an input changes."""
                full_key = f"{prefix}.{key}" if prefix else key
                try:
                    if app_state.qick_cfg:
                        app_state.qick_cfg.update(full_key, value, q_index=app_state.selected_qubit)
                        ui.notify(f"Updated {full_key} to {value}", type="positive")
                        
                        # Update local view config to reflect changes
                        # We don't need to reload everything, just update the local dict reference if needed
                        # But qick_cfg.update handles the backend. 
                        # app_state.view_cfg is a reference to the config dict, so it might be updated in place if qick_cfg modifies it.
                        # However, qick_cfg.read_config returns a clean copy.
                        # Let's re-read to be safe and consistent.
                        new_cfg = app_state.read_config(app_state.selected_qubit)
                        app_state.view_cfg = new_cfg
                        
                    else:
                        ui.notify("Config system not initialized.", type="negative")
                except Exception as e:
                    ui.notify(f"Error updating config: {str(e)}", type="negative")

            def render_dict(title, d, prefix=""):
                if not d:
                    return
                with ui.expansion(title, value=False).classes("bg-white shadow-sm"):
                    with ui.column().classes("gap-2 p-2"):
                        for k, v in d.items():
                            # Determine input type based on value type
                            if isinstance(v, bool):
                                ui.checkbox(text=k, value=v, on_change=lambda e, key=k: update_config(key, e.value, prefix))
                            elif isinstance(v, (int, float)):
                                # Use number input for numeric values
                                # Use appropriate step/format if possible, but generic is fine
                                ui.number(label=k, value=v, on_change=lambda e, key=k: update_config(key, e.value, prefix)).classes("w-full")
                            else:
                                # Fallback to text input for strings or other types
                                ui.input(label=k, value=str(v), on_change=lambda e, key=k: update_config(key, e.value, prefix)).classes("w-full")

            render_dict("CH", cfg.get("ch", {}), "ch")
            render_dict("RES", cfg.get("res", {}), "res")
            render_dict("QB", cfg.get("qb", {}), "qb")
            render_dict("COOLING", cfg.get("cooling", {}), "cooling")

            # Experiment config is flat in the main list but we group it here.
            # Updating these requires handling them as top-level keys for this qubit config.
            # The prefix should be empty or handled specifically.
            # Since app_state.view_cfg is the qubit config (flat-ish structure from read_config),
            # keys like 'reps' are at the top level of that dict.
            # So prefix="" is correct for them.
            
            exp_cfg = {
                "reps": cfg.get("reps"),
                "trig_time": cfg.get("trig_time"),
                "relax_delay": cfg.get("relax_delay"),
            }
            # Filter out None values to avoid displaying empty inputs if keys are missing
            exp_cfg = {k: v for k, v in exp_cfg.items() if v is not None}
            
            render_dict("EXPERIMENT CONFIG", exp_cfg, "")

        config_view()
        
        # Bind refresh method to app_state for external access
        def refresh_sidebar():
            config_view.refresh()
            
        app_state.sidebar_refresh = refresh_sidebar
