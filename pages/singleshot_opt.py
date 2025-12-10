from nicegui import ui
from layout.base_page import BaseMeasurementController, create_measurement_page
from state.singleshot_opt_state import SingleshotOptState
from qick_workspace.scrip.s000_SingleShot_ge_prog_opt import SingleShot_ge_opt
import numpy as np
from datetime import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from state.app_state import AppState


class SingleshotOptController(BaseMeasurementController):
    """Controller for Single Shot Optimize measurement."""

    def __init__(self, app_state: 'AppState', singleshot_opt_state: SingleshotOptState):
        super().__init__(app_state, singleshot_opt_state)

    def prepare_config(self, current_cfg: Dict[str, Any]):
        config = self.app_state.get_qubit(self.app_state.selected_qubit)
        config["shots"] = int(self.state.shot_num)
        
        # Always set freq_center from config
        self.state.freq_center = config["res_freq_ge"]
        
        return config

    def update_result(self):
        """Update config with optimized parameters."""
        if self.state.opt_freq is not None:
            try:
                if self.app_state.qick_cfg:
                    self.app_state.qick_cfg.update("res.res_freq_ge", self.state.opt_freq, q_index=self.app_state.selected_qubit)
                    ui.notify(f"Updated res_freq_ge to {self.state.opt_freq:.4f} MHz", type="positive")
            except Exception as e:
                ui.notify(f"Error updating freq: {str(e)}", type="negative")
                
        if self.state.opt_gain is not None:
            try:
                if self.app_state.qick_cfg:
                    self.app_state.qick_cfg.update("res.res_gain_ge", self.state.opt_gain, q_index=self.app_state.selected_qubit)
                    ui.notify(f"Updated res_gain_ge to {self.state.opt_gain:.4f}", type="positive")
            except Exception as e:
                ui.notify(f"Error updating gain: {str(e)}", type="negative")
                
        if self.state.opt_length is not None:
            try:
                if self.app_state.qick_cfg:
                    self.app_state.qick_cfg.update("res.ro_length", self.state.opt_length, q_index=self.app_state.selected_qubit)
                    ui.notify(f"Updated ro_length to {self.state.opt_length:.4f} us", type="positive")
            except Exception as e:
                ui.notify(f"Error updating length: {str(e)}", type="negative")
        
        # Reload config and refresh sidebar
        try:
            new_cfg = self.app_state.read_config(self.app_state.selected_qubit)
            self.app_state.view_cfg = new_cfg
            if self.app_state.sidebar_refresh:
                self.app_state.sidebar_refresh()
        except Exception as e:
            print(f"Error refreshing sidebar: {e}")

    def update_fit_plot(self, x_data, y_data):
        """Display optimization results."""
        if self.fit_plot_container is None:
            return

        self.fit_plot_container.clear()
        
        if self.state.fid_array is None:
            return
            
        with self.fit_plot_container:
            with ui.matplotlib(figsize=(14, 10)).figure as fig:
                # Create 3D visualization of fidelity
                fid_array = self.state.fid_array
                
                # Find best point
                max_idx = np.unravel_index(np.argmax(fid_array), fid_array.shape)
                
                # Create subplots for each 2D slice
                fig.suptitle(f"Readout Optimization Results (Max Fidelity: {self.state.max_fidelity:.4f})", fontsize=14)
                
                # Frequency vs Gain (averaged over length)
                ax1 = fig.add_subplot(2, 2, 1)
                freq_gain_fid = np.mean(fid_array, axis=0)
                freq_axis = np.linspace(self.state.freq_center - self.state.freq_span/2, 
                                       self.state.freq_center + self.state.freq_span/2, 
                                       self.state.freq_steps)
                gain_axis = np.linspace(self.state.gain_start, self.state.gain_stop, self.state.gain_steps)
                
                im1 = ax1.imshow(freq_gain_fid.T, aspect='auto', origin='lower',
                               extent=[freq_axis[0], freq_axis[-1], gain_axis[0], gain_axis[-1]],
                               cmap='viridis')
                ax1.set_xlabel('Frequency (MHz)')
                ax1.set_ylabel('Gain')
                ax1.set_title('Freq vs Gain (avg over length)')
                fig.colorbar(im1, ax=ax1, label='Fidelity')
                if self.state.opt_freq and self.state.opt_gain:
                    ax1.plot(self.state.opt_freq, self.state.opt_gain, 'r*', markersize=15, label='Optimum')
                    ax1.legend()
                
                # Frequency vs Length (averaged over gain)
                ax2 = fig.add_subplot(2, 2, 2)
                freq_length_fid = np.mean(fid_array, axis=1)
                length_axis = np.linspace(self.state.length_start, self.state.length_stop, self.state.length_steps)
                
                im2 = ax2.imshow(freq_length_fid.T, aspect='auto', origin='lower',
                               extent=[freq_axis[0], freq_axis[-1], length_axis[0], length_axis[-1]],
                               cmap='viridis')
                ax2.set_xlabel('Frequency (MHz)')
                ax2.set_ylabel('Length (us)')
                ax2.set_title('Freq vs Length (avg over gain)')
                fig.colorbar(im2, ax=ax2, label='Fidelity')
                if self.state.opt_freq and self.state.opt_length:
                    ax2.plot(self.state.opt_freq, self.state.opt_length, 'r*', markersize=15, label='Optimum')
                    ax2.legend()
                
                # Gain vs Length (averaged over frequency)
                ax3 = fig.add_subplot(2, 2, 3)
                gain_length_fid = np.mean(fid_array, axis=2)
                
                im3 = ax3.imshow(gain_length_fid.T, aspect='auto', origin='lower',
                               extent=[length_axis[0], length_axis[-1], gain_axis[0], gain_axis[-1]],
                               cmap='viridis')
                ax3.set_xlabel('Length (us)')
                ax3.set_ylabel('Gain')
                ax3.set_title('Length vs Gain (avg over freq)')
                fig.colorbar(im3, ax=ax3, label='Fidelity')
                if self.state.opt_length and self.state.opt_gain:
                    ax3.plot(self.state.opt_length, self.state.opt_gain, 'r*', markersize=15, label='Optimum')
                    ax3.legend()
                
                # Results text
                ax4 = fig.add_subplot(2, 2, 4)
                ax4.axis('off')
                result_text = f"""
Optimization Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maximum Fidelity: {self.state.max_fidelity:.4f}

Optimal Parameters:
  Frequency: {self.state.opt_freq:.4f} MHz
  Gain: {self.state.opt_gain:.6f}
  Length: {self.state.opt_length:.4f} us

Sweep Ranges:
  Freq: {freq_axis[0]:.2f} - {freq_axis[-1]:.2f} MHz ({self.state.freq_steps} steps)
  Gain: {self.state.gain_start:.3f} - {self.state.gain_stop:.3f} ({self.state.gain_steps} steps)
  Length: {self.state.length_start:.3f} - {self.state.length_stop:.3f} us ({self.state.length_steps} steps)

Total measurements: {self.state.freq_steps * self.state.gain_steps * self.state.length_steps}
Shots per point: {self.state.shot_num}
                """
                ax4.text(0.1, 0.5, result_text, fontsize=11, family='monospace',
                        verticalalignment='center')
                
                fig.tight_layout()
                
                if self.update_button:
                    self.update_button.enable()

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
            
            # Prepare sweep parameters based on flags
            if self.state.sweep_freq:
                freq_axis = np.linspace(
                    self.state.freq_center - self.state.freq_span/2,
                    self.state.freq_center + self.state.freq_span/2,
                    int(self.state.freq_steps)
                )
            else:
                freq_axis = np.array([self.state.freq_center])
            
            if self.state.sweep_gain:
                gain_axis = np.linspace(self.state.gain_start, self.state.gain_stop, int(self.state.gain_steps))
            else:
                gain_axis = np.array([config.get("res_gain_ge", 0.2)])
            
            if self.state.sweep_length:
                length_axis = np.linspace(self.state.length_start, self.state.length_stop, int(self.state.length_steps))
            else:
                length_axis = np.array([config.get("res_length", 0.2)])
            
            sweep_para = {
                "freq": freq_axis,
                "gain": gain_axis,
                "length": length_axis
            }
            
            total_points = len(freq_axis) * len(gain_axis) * len(length_axis)
            ui.notify(f"Starting optimization: {len(length_axis)}×{len(gain_axis)}×{len(freq_axis)} = {total_points} points", 
                     type="info")
            
            # Clear and setup progress display
            if self.plot_container:
                self.plot_container.clear()
                with self.plot_container:
                    ui.label(f"Running optimization sweep...").classes("text-lg font-bold")
                    ui.label(f"Total points: {total_points}").classes("text-md")
                    progress_bar = ui.linear_progress(value=0, show_value=True).classes("w-full")
                    progress_label = ui.label("Initializing...").classes("text-sm")
            
            # Run optimization
            optimizer = SingleShot_ge_opt(soc, soccfg, config)
            
            # Define progress callback to update GUI
            def update_progress_callback(current, total):
                if self.plot_container:
                    progress = current / total
                    progress_bar.value = progress
                    progress_label.text = f"Progress: {current}/{total} points ({progress*100:.1f}%)"
            
            # Run the sweep with progress callback
            optimizer.run(int(self.state.shot_num), sweep_para, progress_callback=update_progress_callback)
            
            if self.plot_container:
                progress_bar.value = 0.5
                progress_label.text = "Analyzing results..."
            
            # Analyze results
            opt_length, opt_gain, opt_freq = optimizer.analyze()
            
            if self.plot_container:
                progress_bar.value = 1.0
                progress_label.text = "Complete!"
            
            # Store results
            self.state.opt_freq = opt_freq
            self.state.opt_gain = opt_gain
            self.state.opt_length = opt_length
            self.state.fid_array = optimizer.fid_Array
            self.state.max_fidelity = np.max(optimizer.fid_Array)
            self.state.raw_data = optimizer.data
            self.state.last_plot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update plot
            self.update_fit_plot(None, None)
            
            ui.notify(f"Optimization complete! Max fidelity: {self.state.max_fidelity:.4f}", type="positive")

        except Exception as e:
            ui.notify(f"Error during optimization: {str(e)}", type="negative")
            print(f"Optimization error: {e}")
            traceback.print_exc()

        finally:
            self.on_measurement_finish()


def add_page(app_state):
    """Create the Single Shot Optimize page with custom settings."""
    
    def settings_card(state, app_state_obj, on_run_callback, **kwargs):
        """Custom settings card for optimization parameters."""
        with ui.card().classes("max-w-xs p-4"):
            ui.label("Optimization Settings").classes("text-lg font-semibold mb-2")
            
            # Frequency sweep
            ui.label("Frequency Sweep").classes("font-semibold mt-2")
            freq_checkbox = ui.checkbox("Enable Freq Sweep").bind_value(state, "sweep_freq")
            freq_span_input = ui.number("Span (MHz)", format="%.1f", step=0.5).bind_value(state, "freq_span")
            freq_steps_input = ui.number("Steps", format="%d", step=1, min=3, max=21).bind_value(state, "freq_steps")
            
            # Bind visibility to checkbox
            freq_span_input.bind_visibility_from(state, "sweep_freq")
            freq_steps_input.bind_visibility_from(state, "sweep_freq")
            
            ui.separator()
            
            # Gain sweep
            ui.label("Gain Sweep").classes("font-semibold mt-2")
            gain_checkbox = ui.checkbox("Enable Gain Sweep").bind_value(state, "sweep_gain")
            gain_start_input = ui.number("Start", format="%.3f", step=0.01).bind_value(state, "gain_start")
            gain_stop_input = ui.number("Stop", format="%.3f", step=0.01).bind_value(state, "gain_stop")
            gain_steps_input = ui.number("Steps", format="%d", step=1, min=3, max=15).bind_value(state, "gain_steps")
            
            # Bind visibility to checkbox
            gain_start_input.bind_visibility_from(state, "sweep_gain")
            gain_stop_input.bind_visibility_from(state, "sweep_gain")
            gain_steps_input.bind_visibility_from(state, "sweep_gain")
            
            ui.separator()
            
            # Length sweep
            ui.label("Length Sweep (us)").classes("font-semibold mt-2")
            length_checkbox = ui.checkbox("Enable Length Sweep").bind_value(state, "sweep_length")
            length_start_input = ui.number("Start", format="%.3f", step=0.01).bind_value(state, "length_start")
            length_stop_input = ui.number("Stop", format="%.3f", step=0.01).bind_value(state, "length_stop")
            length_steps_input = ui.number("Steps", format="%d", step=1, min=3, max=15).bind_value(state, "length_steps")
            
            # Bind visibility to checkbox
            length_start_input.bind_visibility_from(state, "sweep_length")
            length_stop_input.bind_visibility_from(state, "sweep_length")
            length_steps_input.bind_visibility_from(state, "sweep_length")
            
            ui.separator()
            
            # Shots
            ui.number("Shots per point", format="%d", step=100, min=100).bind_value(state, "shot_num")
            
            ui.separator()
            
            # Run button
            run_btn = ui.button("Run Optimization", on_click=on_run_callback, color="primary").classes("w-full mt-4")
            
            return run_btn
    
    create_measurement_page(
        page_route="/singleshot_opt",
        page_title="Single Shot Optimize",
        controller_class=SingleshotOptController,
        app_state=app_state,
        state_attr="singleshot_opt_state",
        settings_card_func=settings_card,
        settings_card_kwargs={},
        plot_title="Optimization Progress",
        fit_plot_title="Optimization Results",
        update_button_text="Update Config (Freq, Gain, Length)",
    )
