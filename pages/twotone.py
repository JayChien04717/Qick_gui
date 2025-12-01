
from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.twotone_state import TwoToneState
from qick_workspace.scrip.s003_qubit_spec_ge import PulseProbeSpectroscopyProgram
from layout.nicegui_plot import nicegui_plot, nicegui_plot_final
from qick_workspace.tools.fitting import fitlor, lorfunc

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import frequency_settings_card
from layout.measurement_tools import prepare_config, update_result

if TYPE_CHECKING:
    from state.app_state import AppState


class TwoToneController(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the Two-tone page."""

    def __init__(self, app_state: 'AppState', twotone_state: TwoToneState):
        super().__init__(app_state, twotone_state)
        # Auto-update center freq
        try:
            raw_cfg = app_state.current_cfg
            if raw_cfg:
                qb_freq = raw_cfg.get("qb", {}).get("qb_freq_ge")
                if isinstance(qb_freq, (int, float)):
                    twotone_state.center_freq = qb_freq
        except Exception:
            pass

    def prepare_config(self, current_cfg: Dict[str, Any]):
        return prepare_config(
            self.state, 
            current_cfg, 
            param_name="qb_freq_ge", 
        )

    def update_result(self):
        if self.state.fit_results and 'fr' in self.state.fit_results:
            update_result(self.app_state, self.state.fit_results['fr'], "qb.qb_freq_ge")
            update_result(self.app_state, self.state.fit_results['fr'], "qb.qb_mixer")
        else:
            ui.notify("No fit results available", type="warning")

    def update_fit_plot(self, freqs, iq_data):
        if self.fit_plot_container is None:
            return
        
        self.fit_plot_container.clear()
        if freqs is None or iq_data is None or len(freqs) != len(iq_data):
            return

        try:
            with self.fit_plot_container:
                with ui.matplotlib(figsize=(12, 6)).figure as fig:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    title = f"Qubit Fit (Time: {timestamp})"
                    
                    fit_params, error, _ = nicegui_plot_final(
                        freqs, 
                        iq_data, 
                        "Frequency (MHz)", 
                        fitlor, 
                        lorfunc,
                        fig=fig,
                        title=title
                    )
                    
                    # Update title with fitted frequency
                    if fit_params is not None:
                        fig.suptitle(f"Qubit ge Spectrum, Qubit freq = {fit_params[2]:.6f} MHz")
                
                # fit_params for lorfunc are [y0, yscale, x0, xscale]
                # x0 (index 2) is the resonance frequency
                fres = fit_params[2]
                self.state.fit_results = {'fr': fres, 'params': fit_params, 'error': error}
                
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
            
            prog = PulseProbeSpectroscopyProgram(
                soccfg,
                reps=config["reps"],
                final_delay=config["relax_delay"],
                cfg=config,
            )

            freqs = prog.get_pulse_param("qb_pulse", "freq", as_array=True)

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
                (line,) = ax.plot(freqs, np.zeros_like(freqs), "o-", markersize=4)
                ax.set_xlabel("Freq (MHz)")
                ax.set_ylabel("|IQ|")
                ax.set_title("Two-tone Result (Initializing...)")

        def plot_callback(data: np.ndarray, avg_count: int):
            line.set_ydata(data)
            current_min, current_max = np.min(data), np.max(data)
            if current_max > current_min:
                ax.set_ylim(current_min * 0.95, current_max * 1.05)
            ax.set_title(f"Two-tone Result (Avg: {avg_count})")
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
            self.state.freqs = freqs
            self.state.iq_data = iq_data
            self.state.last_plot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.update_fit_plot(freqs, iq_data)
                
        except Exception as e:
            ui.notify(f"Error during acquisition: {str(e)}", type="negative")
            print(f"Two-tone error: {e}")
            traceback.print_exc()
        
        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/twotone",
        page_title="Two-tone Measurement",
        controller_class=TwoToneController,
        app_state=app_state,
        state_attr="twotone_state",
        settings_card_func=frequency_settings_card,
        settings_card_kwargs={"change_variable": "qb_freq_ge"},
        plot_title="Two-tone Result",
        fit_plot_title="Qubit Fit",
    )
