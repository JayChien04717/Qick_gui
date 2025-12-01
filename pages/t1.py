from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.t1_state import T1State
from qick_workspace.scrip.s008_T1_ge import T1Program
from layout.nicegui_plot import nicegui_plot, nicegui_plot_final
from qick_workspace.tools.fitting import fitexp, expfunc

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import wait_settings_card
from layout.measurement_tools import prepare_config, update_result

if TYPE_CHECKING:
    from state.app_state import AppState


class T1Controller(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the T1 page."""

    def __init__(self, app_state: 'AppState', t1_state: T1State):
        super().__init__(app_state, t1_state)

    def prepare_config(self, current_cfg: Dict[str, Any]):
        config = prepare_config(
            self.state, 
            current_cfg, 
            param_name="wait_time", 
            sweep_type="wait"
        )
        return config

    def update_result(self):
        # T1 measurement usually doesn't update any config parameter automatically
        # unless we want to track T1 over time?
        # For now, just notify.
        if self.state.fit_results and 'params' in self.state.fit_results:
             ui.notify("T1 Fit Updated", type="info")
        else:
            ui.notify("No fit results available", type="warning")

    def update_fit_plot(self, times, iq_data):
        if self.fit_plot_container is None:
            return
        
        self.fit_plot_container.clear()
        if times is None or iq_data is None or len(times) != len(iq_data):
            return

        try:
            with self.fit_plot_container:
                with ui.matplotlib(figsize=(12, 6)).figure as fig:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    title = f"T1 Fit (Time: {timestamp})"
                    
                    fit_params, error, _ = nicegui_plot_final(
                        times, 
                        iq_data, 
                        "Time (us)", 
                        fitexp, 
                        expfunc,
                        fig=fig,
                        title=title
                    )
                    # T1 = fit_params[2]
                    ui.label(f"T1: {fit_params[2]:.4f} us").classes("text-lg font-bold")
                    
                    self.state.fit_results = {
                        'params': fit_params, 
                        'error': error
                    }
                
                if self.update_button:
                    self.update_button.enable()

        except Exception as e:
            with self.fit_plot_container:
                ui.label(f"Fitting Error: {str(e)}").classes("text-red-500")
            print(f"Fitting Error: {e}")
            traceback.print_exc()

    async def run_measurement(self):
        self.on_measurement_start()

        if not self.app_state.instrument_connected:
            ui.notify("Not connected to QICK!", type="negative")
            if self.run_button: self.run_button.enable()
            return

        soc = self.app_state.soc
        soccfg = self.app_state.soccfg
        
        try:
            current_cfg = self.app_state.get_qubit(self.app_state.selected_qubit)
            config = self.prepare_config(current_cfg)

            prog = T1Program(
                soccfg,
                reps=config["reps"],
                final_delay=config["relax_delay"],
                cfg=config,
            )

            times = prog.get_time_param("wait", "t", as_array=True)

        except Exception as e:
            ui.notify(f"Configuration Error: {e}", type="negative")
            print(f"Configuration Error: {e}")
            if self.run_button: self.run_button.enable()
            return
        
        # Prepare Live Plot
        if self.plot_container is None:
            if self.run_button: self.run_button.enable()
            return
        
        self.plot_container.clear()
        with self.plot_container:
            fig_element = ui.matplotlib(figsize=(9, 4))
            with fig_element.figure as fig:
                ax = fig.gca()
                (line,) = ax.plot(times, np.zeros_like(times), "o-", markersize=4)
                ax.set_xlabel("Time (us)")
                ax.set_ylabel("|IQ|")
                ax.set_title("T1 Result (Initializing...)")

        def plot_callback(data: np.ndarray, avg_count: int):
            line.set_ydata(data)
            current_min, current_max = np.min(data), np.max(data)
            if current_max > current_min:
                ax.set_ylim(current_min * 0.95, current_max * 1.05)
            ax.set_title(f"T1 Result (Avg: {avg_count})")
            fig_element.update()
            
        def update_progress(current: int, total: int, remaining: float):
            percent = (current / total) * 100
            etr_text = f"{remaining:.1f}s" if remaining is not None else "?"
            if self.progress_info_label:
                self.progress_info_label.text = f"{percent:.1f}% (ETR: {etr_text})"
            if self.progress_bar:
                self.progress_bar.value = current / total
            
        try:
            iq_data, interrupted = await nicegui_plot(
                prog=prog,
                soc=soc,
                py_avg=int(self.state.py_avg),
                plot_callback=plot_callback,
                progress_callback=update_progress,
            )
            
            if interrupted:
                 ui.notify("Acquisition Interrupted!", type="warning")
            else:
                 ui.notify("Acquisition Done!", type="positive")

            # Save State
            self.state.iq_data = iq_data
            self.state.times = times
            self.state.last_plot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.update_fit_plot(times, iq_data)

        except Exception as e:
            ui.notify(f"Error during acquisition: {str(e)}", type="negative")
            print(f"T1 error: {e}")
            traceback.print_exc()
        
        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/t1",
        page_title="T1 Measurement",
        controller_class=T1Controller,
        app_state=app_state,
        state_attr="t1_state",
        settings_card_func=wait_settings_card,
        settings_card_kwargs={},
        plot_title="T1 Result",
        fit_plot_title="T1 Fit",
        update_button_text="Update Result (no need update)",
    )
