from nicegui import ui
from typing import Callable, Any

def frequency_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str, **kwargs):
    """
    Renders the 'Frequency Parameters' card for the One-tone measurement.
    
    This function modularizes the UI code, making the main page file cleaner.
    It handles the layout, data binding, and interaction logic for the settings.

    Args:
        onetone_state: The persistent state object for One-tone settings.
        app_state: The global application state (for config access).
        on_run_callback: A function to be called when the 'RUN' button is clicked.
                         It should accept one argument: the status label element.
    """
    
    # Use ui.card() to create a contained visual block with shadow and padding.
    # classes('max-w-xs'): Limits the width to extra small (approx 20rem/320px) 
    # to keep it compact on the left side.
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        # --- Sweep Mode Selection ---
        # ui.select creates a dropdown menu.
        # options: A dictionary {value: label} maps internal values to display text.
        # bind_value: Two-way binding. When the user selects an option, 
        #             onetone_state.sweep_mode is updated automatically.
        #             Conversely, if the state changes elsewhere, the dropdown updates.
        ui.select(
            options={
                "start_stop": "Start – Stop",
                "center_span": "Center – Span",
            },
            value=state.sweep_mode,
            label="Sweep mode",
        ).bind_value(state, "sweep_mode")

        # --- Start / Stop Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'start_stop'.
        # bind_visibility_from: Dynamically shows/hides the element based on the lambda condition.
        #                       If onetone_state.sweep_mode == 'start_stop', it returns True (visible).
        
        ui.number("Start freq (MHz)").bind_value(
            state, "start_freq"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "start_stop",
        )

        ui.number("Stop freq (MHz)").bind_value(
            state, "stop_freq"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "start_stop",
        )

        # --- Center / Span Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'center_span'.
        
        # We use a row to place the Center input and the Fetch button side-by-side.
        with ui.row().classes("w-full items-center gap-1").bind_visibility_from(
            state,  
            "sweep_mode",
            lambda m: m == "center_span",
        ):
            # The input takes up available space (flex-1).
            ui.number("Center (MHz)").bind_value(
                state, "center_freq"
            ).classes("flex-1")

            # --- Fetch Logic ---
            # This local function handles fetching the frequency from the global config.
            def fetch_center():
                try:
                    cfg = app_state.current_cfg
                    if cfg:
                        # Access the nested dictionary structure safely
                        freq = cfg.get("res", {}).get(change_variable)
                        # Or direct access if structure is guaranteed: cfg['res_freq_ge']
                        # Based on user's previous edit, it might be flat or nested. 
                        # Let's try the safer nested approach first, or fallback if needed.
                        # Actually, user's last edit used cfg['res_freq_ge'], let's support that if possible
                        # but usually it's in a sub-dict. Let's stick to the safe way or check both.
                        if freq is None and change_variable in cfg:
                             freq = cfg[change_variable]

                        if isinstance(freq, (int, float)):
                            state.center_freq = freq
                            ui.notify(f"Updated Center to {freq} MHz", type="positive")
                        else:
                            ui.notify("Invalid frequency in config", type="warning")
                    else:
                        ui.notify("No config loaded", type="warning")
                except Exception as e:
                    ui.notify(f"Error fetching center: {e}", type="negative")

            # The button triggers the fetch logic.
            # props('flat round dense'): Styling for a minimal, circular button.
            # tooltip: Shows text on hover.
            ui.button(icon="refresh", on_click=fetch_center).props(
                "flat round dense"
            ).tooltip("Fetch from Config")

        ui.number("Span (MHz)").bind_value(
            state, "span"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "center_span",
        )

        # --- Common Parameters ---
        # format="%d": Ensures the display is an integer (no decimal points).
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("Gain (a.u)").bind_value(state, "gain")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # --- Run Button ---
        # on_click: Calls the callback provided by the parent page.
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")
        
        return run_btn


def gain_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str, **kwargs):
    """
    Renders the 'Gain Parameters' card for the One-tone measurement.
    
    This function modularizes the UI code, making the main page file cleaner.
    It handles the layout, data binding, and interaction logic for the settings.

    Args:
        onetone_state: The persistent state object for One-tone settings.
        app_state: The global application state (for config access).
        on_run_callback: A function to be called when the 'RUN' button is clicked.
                         It should accept one argument: the status label element.
    """
    
    # Use ui.card() to create a contained visual block with shadow and padding.
    # classes('max-w-xs'): Limits the width to extra small (approx 20rem/320px) 
    # to keep it compact on the left side.
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        # --- Sweep Mode Selection ---
        # ui.select creates a dropdown menu.
        # options: A dictionary {value: label} maps internal values to display text.
        # bind_value: Two-way binding. When the user selects an option, 
        #             onetone_state.sweep_mode is updated automatically.
        #             Conversely, if the state changes elsewhere, the dropdown updates.
        ui.select(
            options={
                "arb": "Arbitrary",
                "flat_top": "Flat Top",
            },
            value=state.pulse_type,
            label="Pulse type",
        ).bind_value(state, "pulse_type")

        # --- Start / Stop Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'start_stop'.
        # bind_visibility_from: Dynamically shows/hides the element based on the lambda condition.
        #                       If onetone_state.sweep_mode == 'start_stop', it returns True (visible).
        
        ui.number("Start gain (a.u)").bind_value(
            state, "start_gain"
        )

        ui.number("Stop gain (a.u)").bind_value(
            state, "stop_gain"
        )

        # --- Center / Span Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'center_span'.
        
        # We use a row to place the Center input and the Fetch button side-by-side.
        with ui.row().classes("w-full items-center gap-1").bind_visibility_from(
            state,  
            "pulse_type",
            lambda m: m == "flat_top",
        ):
            # The input takes up available space (flex-1).
            ui.number("Flat top len (us)").bind_value(
                state, "flat_top_len"
            ).classes("flex-1")

    
        # --- Common Parameters ---
        # format="%d": Ensures the display is an integer (no decimal points).
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("sigma").bind_value(state, "sigma")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # --- Run Button ---
        # on_click: Calls the callback provided by the parent page.
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")

        
        return run_btn


def wait_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str = None, **kwargs):
    """
    Renders the 'Wait Parameters' card for time-domain measurements (e.g. Ramsey, T1).
    """
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        ui.number("Start Time (us)").bind_value(state, "start_time")
        ui.number("Stop Time (us)").bind_value(state, "stop_time")
        
        # Optional Ramsey Freq (only if state has it)
        if hasattr(state, "ramsey_freq"):
            ui.number("Ramsey Freq (MHz)").bind_value(state, "ramsey_freq")

        # Common Parameters
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # Run Button
        #             Conversely, if the state changes elsewhere, the dropdown updates.
        ui.select(
            options={
                "start_stop": "Start – Stop",
                "center_span": "Center – Span",
            },
            value=state.sweep_mode,
            label="Sweep mode",
        ).bind_value(state, "sweep_mode")

        # --- Start / Stop Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'start_stop'.
        # bind_visibility_from: Dynamically shows/hides the element based on the lambda condition.
        #                       If onetone_state.sweep_mode == 'start_stop', it returns True (visible).
        
        ui.number("Start freq (MHz)").bind_value(
            state, "start_freq"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "start_stop",
        )

        ui.number("Stop freq (MHz)").bind_value(
            state, "stop_freq"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "start_stop",
        )

        # --- Center / Span Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'center_span'.
        
        # We use a row to place the Center input and the Fetch button side-by-side.
        with ui.row().classes("w-full items-center gap-1").bind_visibility_from(
            state,  
            "sweep_mode",
            lambda m: m == "center_span",
        ):
            # The input takes up available space (flex-1).
            ui.number("Center (MHz)").bind_value(
                state, "center_freq"
            ).classes("flex-1")

            # --- Fetch Logic ---
            # This local function handles fetching the frequency from the global config.
            def fetch_center():
                try:
                    cfg = app_state.current_cfg
                    if cfg:
                        # Access the nested dictionary structure safely
                        freq = cfg.get("res", {}).get(change_variable)
                        # Or direct access if structure is guaranteed: cfg['res_freq_ge']
                        # Based on user's previous edit, it might be flat or nested. 
                        # Let's try the safer nested approach first, or fallback if needed.
                        # Actually, user's last edit used cfg['res_freq_ge'], let's support that if possible
                        # but usually it's in a sub-dict. Let's stick to the safe way or check both.
                        if freq is None and change_variable in cfg:
                             freq = cfg[change_variable]

                        if isinstance(freq, (int, float)):
                            state.center_freq = freq
                            ui.notify(f"Updated Center to {freq} MHz", type="positive")
                        else:
                            ui.notify("Invalid frequency in config", type="warning")
                    else:
                        ui.notify("No config loaded", type="warning")
                except Exception as e:
                    ui.notify(f"Error fetching center: {e}", type="negative")

            # The button triggers the fetch logic.
            # props('flat round dense'): Styling for a minimal, circular button.
            # tooltip: Shows text on hover.
            ui.button(icon="refresh", on_click=fetch_center).props(
                "flat round dense"
            ).tooltip("Fetch from Config")

        ui.number("Span (MHz)").bind_value(
            state, "span"
        ).bind_visibility_from(
            state,
            "sweep_mode",
            lambda m: m == "center_span",
        )

        # --- Common Parameters ---
        # format="%d": Ensures the display is an integer (no decimal points).
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("Gain (a.u)").bind_value(state, "gain")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # --- Run Button ---
        # on_click: Calls the callback provided by the parent page.
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")
        
        return run_btn


def gain_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str, **kwargs):
    """
    Renders the 'Gain Parameters' card for the One-tone measurement.
    
    This function modularizes the UI code, making the main page file cleaner.
    It handles the layout, data binding, and interaction logic for the settings.

    Args:
        onetone_state: The persistent state object for One-tone settings.
        app_state: The global application state (for config access).
        on_run_callback: A function to be called when the 'RUN' button is clicked.
                         It should accept one argument: the status label element.
    """
    
    # Use ui.card() to create a contained visual block with shadow and padding.
    # classes('max-w-xs'): Limits the width to extra small (approx 20rem/320px) 
    # to keep it compact on the left side.
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        # --- Sweep Mode Selection ---
        # ui.select creates a dropdown menu.
        # options: A dictionary {value: label} maps internal values to display text.
        # bind_value: Two-way binding. When the user selects an option, 
        #             onetone_state.sweep_mode is updated automatically.
        #             Conversely, if the state changes elsewhere, the dropdown updates.
        ui.select(
            options={
                "arb": "Arbitrary",
                "flat_top": "Flat Top",
            },
            value=state.pulse_type,
            label="Pulse type",
        ).bind_value(state, "pulse_type")

        # --- Start / Stop Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'start_stop'.
        # bind_visibility_from: Dynamically shows/hides the element based on the lambda condition.
        #                       If onetone_state.sweep_mode == 'start_stop', it returns True (visible).
        
        ui.number("Start gain (a.u)").bind_value(
            state, "start_gain"
        )

        ui.number("Stop gain (a.u)").bind_value(
            state, "stop_gain"
        )

        # --- Center / Span Mode Inputs ---
        # These inputs are only visible when sweep_mode is 'center_span'.
        
        # We use a row to place the Center input and the Fetch button side-by-side.
        with ui.row().classes("w-full items-center gap-1").bind_visibility_from(
            state,  
            "pulse_type",
            lambda m: m == "flat_top",
        ):
            # The input takes up available space (flex-1).
            ui.number("Flat top len (us)").bind_value(
                state, "flat_top_len"
            ).classes("flex-1")

    
        # --- Common Parameters ---
        # format="%d": Ensures the display is an integer (no decimal points).
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("sigma").bind_value(state, "sigma")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # --- Run Button ---
        # on_click: Calls the callback provided by the parent page.
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")

        
        return run_btn


def wait_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str = None, **kwargs):
    """
    Renders the 'Wait Parameters' card for time-domain measurements (e.g. Ramsey, T1).
    """
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        ui.number("Start Time (us)").bind_value(state, "start_time")
        ui.number("Stop Time (us)").bind_value(state, "stop_time")
        
        # Optional Ramsey Freq (only if state has it)
        if hasattr(state, "ramsey_freq"):
            ui.number("Ramsey Freq (MHz)").bind_value(state, "ramsey_freq")

        # Common Parameters
        ui.number("Steps", format="%d").bind_value(state, "steps")
        ui.number("Py avg", format="%d").bind_value(state, "py_avg")

        # Run Button
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")
        
        return run_btn


def shot_settings_card(state: Any, app_state: Any, on_run_callback: Callable, change_variable: str = None, on_change: Callable = None, **kwargs):
    """
    Renders the 'Wait Parameters' card for time-domain measurements (e.g. Ramsey, T1).
    """
    with ui.card().classes("max-w-xs"):
        ui.label("Sweep Parameters").classes("font-semibold mb-2")

        ui.number("# of Shots").bind_value(state, "shot_num")
        
        ui.checkbox("Fid Avg").bind_value(state, "fid_avg").on_value_change(on_change)
        ui.checkbox("Fit").bind_value(state, "fit").on_value_change(on_change)
        ui.checkbox("Gauss Overlap").bind_value(state, "gauss_overlap").on_value_change(on_change)
        ui.checkbox("Plot Overlap").bind_value(state, "plotoverlap").on_value_change(on_change)

        # Run Button
        run_btn = ui.button("RUN", on_click=on_run_callback, color="primary").classes("mt-3")
        
        return run_btn