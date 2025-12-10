from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.ramsey_state import RamseyState
from qick_workspace.scrip.s006_Ramsey_ge import RamseyProgram
from layout.nicegui_plot import nicegui_plot, nicegui_plot_final
from qick_workspace.tools.fitting import fitdecaysin, decaysin, fitexp, expfunc

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import wait_settings_card
from layout.measurement_tools import prepare_config, update_result

if TYPE_CHECKING:
    from state.app_state import AppState


class RamseyController(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the Ramsey page."""

    def __init__(self, app_state: "AppState", ramsey_state: RamseyState):
        super().__init__(app_state, ramsey_state)

    def prepare_config(self, current_cfg: Dict[str, Any]):
        config = prepare_config(
            self.state, current_cfg, param_name="wait_time", sweep_type="wait"
        )

        config["ramsey_freq"] = self.state.ramsey_freq
        return config

    def update_result(self):
        if self.state.fit_results and "params" in self.state.fit_results:
            params = self.state.fit_results["params"]
            # params: [yscale, freq, phase_deg, decay, y0] for decaysin
            # freq is detuning frequency.

            ramsey_freq = float(self.state.ramsey_freq)
            detuning = float(params[1])

            if abs(detuning - ramsey_freq) > 0.005:
                # Fetch the current qubit config
                current_cfg = self.app_state.get_qubit(self.app_state.selected_qubit)
                current_qb_freq = float(current_cfg["qb_freq_ge"])

                new_qb_freq = current_qb_freq - (detuning - ramsey_freq)
                update_result(self.app_state, new_qb_freq, "qb.qb_freq_ge")
                update_result(self.app_state, new_qb_freq, "qb.qb_mixer")
            else:
                ui.notify("Detuning < 5kHz, no update needed", type="info")
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
                    title = f"Ramsey Fit (Time: {timestamp})"

                    if self.state.ramsey_freq != 0:
                        fit_params, error, _ = nicegui_plot_final(
                            times,
                            iq_data,
                            "Time (us)",
                            fitdecaysin,
                            decaysin,
                            fig=fig,
                            title=title,
                        )
                        # T2 = fit_params[3]
                        ui.label(
                            f"T2: {fit_params[3]:.4f} us, Detuning: {fit_params[1]:.4f} MHz"
                        ).classes("text-lg font-bold")
                    else:
                        fit_params, error, _ = nicegui_plot_final(
                            times,
                            iq_data,
                            "Time (us)",
                            fitexp,
                            expfunc,
                            fig=fig,
                            title=title,
                        )
                        # T2 = fit_params[2]
                        ui.label(f"T2: {fit_params[2]:.4f} us").classes(
                            "text-lg font-bold"
                        )

                    self.state.fit_results = {"params": fit_params, "error": error}

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

            prog = RamseyProgram(
                soccfg,
                reps=config["reps"],
                final_delay=config["relax_delay"],
                cfg=config,
            )

            times = prog.get_time_param("wait", "t", as_array=True)

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
                (line,) = ax.plot(times, np.zeros_like(times), "o-", markersize=4)
                ax.set_xlabel("Time (us)")
                ax.set_ylabel("|IQ|")
                ax.set_title("Ramsey Result (Initializing...)")

        def plot_callback(data: np.ndarray, avg_count: int):
            line.set_ydata(data)
            current_min, current_max = np.min(data), np.max(data)
            if current_max > current_min:
                ax.set_ylim(current_min * 0.95, current_max * 1.05)
            ax.set_title(f"Ramsey Result (Avg: {avg_count})")
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
            print(f"Ramsey error: {e}")
            traceback.print_exc()

        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/ramsey",
        page_title="Ramsey Measurement",
        controller_class=RamseyController,
        app_state=app_state,
        state_attr="ramsey_state",
        settings_card_func=wait_settings_card,
        settings_card_kwargs={},
        plot_title="Ramsey Result",
        fit_plot_title="Ramsey Fit",
        update_button_text="Update Result (Freq)",
    )
