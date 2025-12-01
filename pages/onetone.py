
from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.onetone_state import OneToneState
from qick_workspace.scrip.s002_res_spec_ge import SingleToneSpectroscopyProgram
from layout.nicegui_plot import nicegui_plot
from qick_workspace.tools.resonator_tools import circuit

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import frequency_settings_card
from layout.measurement_tools import prepare_config, update_result

if TYPE_CHECKING:
    from state.app_state import AppState


class OneToneController(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the One-tone page."""

    def __init__(self, app_state: 'AppState', onetone_state: OneToneState):
        super().__init__(app_state, onetone_state)
        # Auto-update center freq
        try:
            raw_cfg = app_state.current_cfg
            if raw_cfg:
                res_freq = raw_cfg.get("res", {}).get("res_freq_ge")
                if isinstance(res_freq, (int, float)):
                    onetone_state.center_freq = res_freq
        except Exception:
            pass

    def prepare_config(self, current_cfg: Dict[str, Any]):
        return prepare_config(
            self.state, 
            current_cfg, 
            param_name="res_freq_ge",
            sweep_type="freq"
        )

    def update_result(self):
        if self.state.fit_results and 'fr' in self.state.fit_results:
            update_result(self.app_state, self.state.fit_results['fr'], "res.res_freq_ge")
        else:
            ui.notify("No fit results available", type="warning")

    def update_fit_plot(self, freqs, iq_data):
        if self.fit_plot_container is None:
            return
        
        self.fit_plot_container.clear()
        if freqs is None or iq_data is None or len(freqs) != len(iq_data):
            return

        try:
            port1 = circuit.notch_port()
            port1.add_data(freqs, iq_data)
            port1.autofit()
            self.state.fit_results = port1.fitresults
            fres = port1.fitresults['fr']

            if self.update_button:
                self.update_button.enable()

            with self.fit_plot_container:
                with ui.matplotlib(figsize=(10, 8)).figure as fig:
                    axs = fig.subplots(2, 2)
                    fig.suptitle(f"Resonator Fit (fres = {fres:.4f} MHz)")
                    
                    # IQ Plot
                    axs[0, 0].scatter(
                        port1.z_data_raw.real, port1.z_data_raw.imag, label="rawdata", alpha=0.2, color="C0"
                    )
                    axs[0, 0].plot(
                        port1.z_data_sim.real,
                        port1.z_data_sim.imag,
                        label="fit",
                        lw=2,
                        alpha=0.2,
                        color="C2",
                    )
                    axs[0, 0].scatter(
                        port1.z_data.real, port1.z_data.imag, label="ideal rawdata", lw=2, color="C1"
                    )
                    axs[0, 0].plot(
                        port1.z_data_sim_norm.real,
                        port1.z_data_sim_norm.imag,
                        label="ideal fit",
                        lw=2,
                        color="C3",
                    )
                    axs[0, 0].set_xlabel("Re(S21)")
                    axs[0, 0].set_ylabel("Im(S21)")
                    axs[0, 0].set_title("IQ Plot")
                    axs[0, 0].legend(loc="upper right")

                    # Magnitude Plot
                    axs[0, 1].scatter(
                        freqs, np.abs(port1.z_data_raw), label="rawdata", alpha=0.2, color="C0"
                    )
                    axs[0, 1].plot(
                        freqs, np.abs(port1.z_data_sim), label="fit", alpha=0.2, lw=2, color="C2"
                    )
                    axs[0, 1].scatter(freqs, np.abs(port1.z_data), label="ideal rawdata", color="C1")
                    axs[0, 1].plot(
                        freqs, np.abs(port1.z_data_sim_norm), label="ideal fit", lw=2, color="C3"
                    )
                    axs[0, 1].set_xlabel("f (GHz)")
                    axs[0, 1].set_ylabel("|S21|")
                    axs[0, 1].set_title("Magnitude Plot")
                    axs[0, 1].legend(loc="upper right")

                    # Phase Plot
                    axs[1, 0].scatter(
                        freqs,
                        np.angle(port1.z_data_raw),
                        label="rawdata",
                        alpha=0.2,
                        color="C0",
                    )
                    axs[1, 0].plot(
                        freqs, np.angle(port1.z_data_sim), label="fit", alpha=0.2, lw=2, color="C2"
                    )
                    axs[1, 0].scatter(freqs, np.angle(port1.z_data), label="ideal rawdata", color="C1")
                    axs[1, 0].plot(
                        freqs, np.angle(port1.z_data_sim_norm), label="ideal fit", lw=2, color="C3"
                    )
                    axs[1, 0].set_xlabel("f (GHz)")
                    axs[1, 0].set_ylabel("arg(S21)")
                    axs[1, 0].set_title("Phase Plot")
                    axs[1, 0].legend(loc="upper right")

                    # Remove empty subplot
                    fig.delaxes(axs[1, 1])
                    fig.tight_layout()

        except Exception as e:
            with self.fit_plot_container:
                ui.label(f"Fitting Error: {str(e)}").classes("text-red-500")
            print(f"Fitting Error: {e}")

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
            
            prog = SingleToneSpectroscopyProgram(
                soccfg,
                reps=config["reps"],
                final_delay=config["relax_delay"],
                cfg=config,
            )

            freqs = prog.get_pulse_param("res_pulse", "freq", as_array=True)

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
                ax.set_title("One-tone Result (Initializing...)")

        def plot_callback(data: np.ndarray, avg_count: int):
            line.set_ydata(data)
            current_min, current_max = np.min(data), np.max(data)
            if current_max > current_min:
                ax.set_ylim(current_min * 0.95, current_max * 1.05)
            ax.set_title(f"One-tone Result (Avg: {avg_count})")
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
            print(f"One-tone error: {e}")
            traceback.print_exc()
        
        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/onetone",
        page_title="One-tone Measurement",
        controller_class=OneToneController,
        app_state=app_state,
        state_attr="onetone_state",
        settings_card_func=frequency_settings_card,
        settings_card_kwargs={"change_variable": "res_freq_ge"},
        plot_title="One-tone Result",
        fit_plot_title="Resonator Fit",
    )
