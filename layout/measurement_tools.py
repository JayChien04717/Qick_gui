import copy
from typing import Dict, Any, Optional
from nicegui import ui
from qick.asm_v2 import QickSweep1D
import numpy as np

def prepare_config(state, current_cfg: Dict[str, Any], param_name: str, sweep_type: str = "freq"):
    """
    Prepares the configuration dictionary for the measurement.
    Calculates sweep parameters and updates the config.
    
    Args:
        state: The state object containing sweep parameters.
        current_cfg: The current configuration dictionary.
        param_name: The name of the parameter to sweep.
        sweep_type: The type of sweep ("freq", "gain", "wait"). Defaults to "freq".
    """
    # Deep copy to avoid modifying global state
    # Handle addict.Dict deepcopy issue by converting to dict first
    if hasattr(current_cfg, "to_dict"):
        current_cfg = current_cfg.to_dict()
    
    config = copy.deepcopy(current_cfg)

    # Determine sweep parameters based on sweep_type
    if sweep_type == "freq":
        if state.sweep_mode == "start_stop":
            sweep_start = state.start_freq
            sweep_stop = state.stop_freq
        else:  # center_span
            half = state.span / 2
            sweep_start = state.center_freq - half
            sweep_stop = state.center_freq + half
        loop_name = "freqloop"
        
    elif sweep_type == "gain":
        sweep_start = state.start_gain
        sweep_stop = state.stop_gain
        loop_name = "gainloop"
        
    elif sweep_type == "wait":
        sweep_start = state.start_time
        sweep_stop = state.stop_time
        loop_name = "waitloop"
        
    else:
        raise ValueError(f"Invalid sweep_type: {sweep_type}")

    # Update config with sweep parameters
    config[param_name] = QickSweep1D(
        loop_name,
        sweep_start,
        sweep_stop,
    )
    config["steps"] = int(state.steps)
    
    return config   

def update_result(app_state, fit_results: Optional[float], update_para: str):
    """Updates the configuration with the fitted resonant frequency."""
    if fit_results is None:
        ui.notify("No fit results available.", type="warning")
        return
    
    try:        
        # Update the configuration using the qick_cfg object from app_state
        if app_state.qick_cfg:
                app_state.qick_cfg.update(update_para, round(fit_results, 4), q_index=app_state.selected_qubit)
                ui.notify(f"Updated {update_para} to {round(fit_results, 4)} MHz", type="positive")
                
                # Reload config to update view_cfg
                new_cfg = app_state.read_config(app_state.selected_qubit)
                app_state.view_cfg = new_cfg
                
                # Refresh sidebar if available
                if app_state.sidebar_refresh:
                    app_state.sidebar_refresh()
        else:
                ui.notify("Config system not initialized.", type="negative")

    except Exception as e:
        ui.notify(f"Error updating config: {str(e)}", type="negative")
        print(f"Update Error: {e}")
