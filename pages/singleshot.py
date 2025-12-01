from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.singleshot_state import SingleshotState
from qick_workspace.scrip.s000_SingleShot_prog import SingleShotProgram_g, SingleShotProgram_e, hist
from layout.nicegui_plot import nicegui_plot

import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict

from layout.sweep_ui import shot_settings_card
from layout.measurement_tools import prepare_config

if TYPE_CHECKING:
    from state.app_state import AppState


class SingleshotController(BaseMeasurementController):
    """Encapsulates the measurement and plotting logic for the Single Shot page."""

    def __init__(self, app_state: 'AppState', singleshot_state: SingleshotState):
        super().__init__(app_state, singleshot_state)

    def prepare_config(self, current_cfg: Dict[str, Any]):
        config = self.app_state.get_qubit(self.app_state.selected_qubit)
        config["shots"] = self.state.shot_num
        return config

    def update_result(self):
        # Singleshot doesn't update config usually
        pass

    def update_fit_plot(self, x_data, y_data):
        # Singleshot plotting is handled in run_measurement via hist()
        pass

    def on_settings_change(self):
        """Called when settings change (e.g. checkboxes)."""
        self.update_plot()

    def update_plot(self):
        """Re-plot the data using current settings."""
        if not self.state.raw_data:
            return

        if self.plot_container:
            self.plot_container.clear()
            with self.plot_container:
                # Create a matplotlib figure with larger size for better layout
                with ui.matplotlib(figsize=(12, 8)).figure as fig:
                    result = hist(
                        data=self.state.raw_data,
                        plot=True,
                        verbose=False,
                        fig=fig,
                        fid_avg=self.state.fid_avg,
                        fit=self.state.fit,
                        gauss_overlap=self.state.gauss_overlap,
                        plotoverlap=self.state.plotoverlap,
                    )
                    # Adjust layout to prevent squeezing
                    fig.tight_layout()
                    
                    # Display results
                    if result:
                        fid = result.get("fidelity", 0)
                        angle = result.get("angle", 0)
                        ui.label(f"Fidelity: {fid*100:.2f}%, Angle: {angle:.2f} deg").classes("text-lg font-bold")
                        
                        # Save results to state
                        self.state.fit_results = result
                        self.state.last_plot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            
            # 1. Run g-state measurement
            prog_g = SingleShotProgram_g(
                soccfg,
                reps=1, # SingleShotProgram uses shots loop, reps=1 usually
                final_delay=config["relax_delay"],
                cfg=config,
            )
            iq_g = prog_g.acquire(soc, rounds=1, progress=True)
            I_g = iq_g[0][0].T[0]
            Q_g = iq_g[0][0].T[1]
            
            # 2. Run e-state measurement
            prog_e = SingleShotProgram_e(
                soccfg,
                reps=1,
                final_delay=config["relax_delay"],
                cfg=config,
            )
            iq_e = prog_e.acquire(soc, rounds=1, progress=True)
            I_e = iq_e[0][0].T[0]
            Q_e = iq_e[0][0].T[1]
            

            # 3. Prepare data for hist()
            data = {
                "Ig": I_g,
                "Qg": Q_g,
                "Ie": I_e,
                "Qe": Q_e,
            }
            
            # Save raw data to state for re-plotting
            self.state.raw_data = data
            
            # 4. Plotting
            self.update_plot()

            ui.notify("Single Shot Measurement Done!", type="positive")

        except Exception as e:
            ui.notify(f"Error during measurement: {str(e)}", type="negative")
            print(f"Single Shot error: {e}")
            traceback.print_exc()
        
        finally:
            self.on_measurement_finish()


def add_page(app_state):
    create_measurement_page(
        page_route="/singleshot",
        page_title="Single Shot Measurement",
        controller_class=SingleshotController,
        app_state=app_state,
        state_attr="singleshot_state",
        settings_card_func=shot_settings_card,
        settings_card_kwargs={},
        plot_title="Single Shot Result",
        fit_plot_title="Fit (Integrated in Plot)",
        update_button_text="Update Result",
    )
