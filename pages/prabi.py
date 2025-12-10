from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.prabi_state import PowerRabiState
from qick_workspace.scrip.s005_power_rabi_ge import AmplitudeRabiProgram
from layout.nicegui_plot import nicegui_plot, nicegui_plot_final
from qick_workspace.tools.fitting import fitdecaysin, decaysin, fix_phase

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import gain_settings_card
from layout.measurement_tools import prepare_config, update_result

if TYPE_CHECKING:
    from state.app_state import AppState


class PowerRabiController(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the Power Rabi page."""

    def __init__(self, app_state: "AppState", prabi_state: PowerRabiState):
        super().__init__(app_state, prabi_state)

    def prepare_config(self, current_cfg: Dict[str, Any]):
        config = prepare_config(
            self.state, current_cfg, param_name="qb_gain_ge", sweep_type="gain"
        )
        # Update config with UI state parameters
        config["sigma"] = self.state.sigma
        config["pulse_type"] = self.state.pulse_type
        if self.state.pulse_type == "flat_top":
            config["qb_flat_top_length_ge"] = self.state.flat_top_len
        
        # Sync sigma to global config and refresh sidebar
        try:
            if self.app_state.qick_cfg:
                self.app_state.qick_cfg.update("qb.sigma", self.state.sigma, q_index=self.app_state.selected_qubit)
                
                # Reload config to update view_cfg
                new_cfg = self.app_state.read_config(self.app_state.selected_qubit)
                self.app_state.view_cfg = new_cfg
                
                # Refresh sidebar if available
                if self.app_state.sidebar_refresh:
                    self.app_state.sidebar_refresh()
        except Exception as e:
            print(f"Warning: Failed to sync sigma to sidebar: {e}")
        
        return config

    def update_result(self):
        if (
            self.state.fit_results
            and "pi_gain" in self.state.fit_results
            and "pi2_gain" in self.state.fit_results
        ):
            update_result(
                self.app_state, self.state.fit_results["pi_gain"], "qb.pi_gain_ge"
            )
            update_result(
                self.app_state, self.state.fit_results["pi2_gain"], "qb.pi2_gain_ge"
            )
            
            # Also update sigma to sidebar
            try:
                if self.app_state.qick_cfg:
                    self.app_state.qick_cfg.update("qb.sigma_ge", self.state.sigma, q_index=self.app_state.selected_qubit)
                    
                    # Reload config to update view_cfg
                    new_cfg = self.app_state.read_config(self.app_state.selected_qubit)
                    self.app_state.view_cfg = new_cfg
                    
                    # Refresh sidebar if available
                    if self.app_state.sidebar_refresh:
                        self.app_state.sidebar_refresh()
                        
                    ui.notify(f"Updated sigma_ge to {self.state.sigma:.4f}", type="positive")
            except Exception as e:
                print(f"Warning: Failed to update sigma: {e}")
        else:
            ui.notify("No fit results available", type="warning")

    def update_fit_plot(self, gains, iq_data):
        if self.fit_plot_container is None:
            return

        self.fit_plot_container.clear()
        if gains is None or iq_data is None or len(gains) != len(iq_data):
            return

        try:
            with self.fit_plot_container:
                with ui.matplotlib(figsize=(12, 6)).figure as fig:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    title = f"Power Rabi Fit (Time: {timestamp})"

                    fit_params, error, _ = nicegui_plot_final(
                        gains,
                        iq_data,
                        "Gain (a.u)",
                        fitdecaysin,
                        decaysin,
                        fig=fig,
                        title=title,
                    )

                    pi_gain, pi2_gain = fix_phase(fit_params)

                    self.state.fit_results = {
                        "pi_gain": pi_gain,
                        "pi2_gain": pi2_gain,
                        "params": fit_params,
                        "error": error,
                    }

                    ui.label(
                        f"Pi Gain: {pi_gain:.6f}, Pi/2 Gain: {pi2_gain:.6f}"
                    ).classes("text-lg font-bold")

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
            if self.run_button:
                self.run_button.enable()
            return

        soc = self.app_state.soc
        soccfg = self.app_state.soccfg

        try:
            current_cfg = self.app_state.get_qubit(self.app_state.selected_qubit)
            config = self.prepare_config(current_cfg)

            prog = AmplitudeRabiProgram(
                soccfg,
                reps=config["reps"],
                final_delay=config["relax_delay"],
                cfg=config,
            )

            gains = prog.get_pulse_param("qb_pulse", "gain", as_array=True)

        except Exception as e:
            ui.notify(f"Configuration Error: {e}", type="negative")
            print(f"Configuration Error: {e}")
            if self.run_button:
                self.run_button.enable()
            return

        # Prepare Live Plot
        if self.plot_container is None:
            if self.run_button:
                self.run_button.enable()
            return

        self.plot_container.clear()
        with self.plot_container:
            fig_element = ui.matplotlib(figsize=(9, 4))
            with fig_element.figure as fig:
                ax = fig.gca()
                (line,) = ax.plot(gains, np.zeros_like(gains), "o-", markersize=4)
                ax.set_xlabel("Gain (a.u)")
                ax.set_ylabel("|IQ|")
                ax.set_title("Power Rabi Result (Initializing...)")

        def plot_callback(data: np.ndarray, avg_count: int):
            line.set_ydata(data)
            current_min, current_max = np.min(data), np.max(data)
            if current_max > current_min:
                ax.set_ylim(current_min * 0.95, current_max * 1.05)
            ax.set_title(f"Power Rabi Result (Avg: {avg_count})")
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
            self.state.gains = gains
            self.state.iq_data = iq_data
            self.state.last_plot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.update_fit_plot(gains, iq_data)

        except Exception as e:
            ui.notify(f"Error during acquisition: {str(e)}", type="negative")
            print(f"Power Rabi error: {e}")
            traceback.print_exc()

        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/prabi",
        page_title="Power Rabi Measurement",
        controller_class=PowerRabiController,
        app_state=app_state,
        state_attr="prabi_state",
        settings_card_func=gain_settings_card,
        settings_card_kwargs={"change_variable": "qb_gain_ge"},
        plot_title="Power Rabi Result",
        fit_plot_title="Rabi Fit",
        update_button_text="Update Result (Pi Gain, Pi/2 Gain)",
    )
