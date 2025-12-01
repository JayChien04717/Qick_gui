
from nicegui import ui
from layout.layout import page_layout
from typing import TYPE_CHECKING, Any, Dict, Callable, Optional, Type
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime
import traceback

if TYPE_CHECKING:
    from state.app_state import AppState

class BaseMeasurementController(ABC):
    """
    Abstract base class for measurement controllers.
    Encapsulates common logic for UI interaction and measurement flow.
    """

    def __init__(self, app_state: 'AppState', state: Any):
        self.app_state = app_state
        self.state = state
        
        # UI Elements (to be bound)
        self.plot_container: Optional[ui.column] = None
        self.fit_plot_container: Optional[ui.column] = None
        self.last_time_label: Optional[ui.label] = None
        self.progress_bar: Optional[ui.linear_progress] = None
        self.progress_info_label: Optional[ui.label] = None
        self.run_button: Optional[ui.button] = None
        self.update_button: Optional[ui.button] = None

    def set_ui_elements(self, plot_container, fit_plot_container, last_time_label, progress_bar, progress_info_label, run_button, update_button):
        """Bind UI elements to the controller."""
        self.plot_container = plot_container
        self.fit_plot_container = fit_plot_container
        self.last_time_label = last_time_label
        self.progress_bar = progress_bar
        self.progress_info_label = progress_info_label
        self.run_button = run_button
        self.update_button = update_button

    @abstractmethod
    def prepare_config(self, current_cfg: Dict[str, Any]):
        """Prepare the configuration for the measurement."""
        pass

    @abstractmethod
    async def run_measurement(self):
        """Execute the measurement."""
        pass

    @abstractmethod
    def update_result(self):
        """Update the configuration with the result."""
        pass

    @abstractmethod
    def update_fit_plot(self, x_data, y_data):
        """Update the fitting plot."""
        pass
    
    def on_measurement_start(self):
        """Common logic to run at the start of a measurement."""
        if self.run_button:
            self.run_button.disable()
        if self.update_button:
            self.update_button.disable()
            
        if self.progress_bar:
            self.progress_bar.value = 0
            self.progress_bar.visible = True
        if self.progress_info_label:
            self.progress_info_label.text = "Initializing..."

    def on_measurement_finish(self):
        """Common logic to run at the end of a measurement."""
        if self.run_button:
            self.run_button.enable()
        
        if self.progress_bar:
            self.progress_bar.value = 1.0
        if self.progress_info_label:
            self.progress_info_label.text = "Completed"
        
        if self.last_time_label and hasattr(self.state, "last_plot_time"):
             self.last_time_label.text = "Last shown: " + self.state.last_plot_time


def create_measurement_page(
    page_route: str,
    page_title: str,
    controller_class: Type[BaseMeasurementController],
    app_state: 'AppState',
    state_attr: str,
    settings_card_func: Callable,
    settings_card_kwargs: Dict[str, Any],
    plot_title: str = "Result",
    fit_plot_title: str = "Fit",
    update_button_text: str = "Update Result",
):
    """
    Generates a standard measurement page.

    Args:
        page_route: The URL route for the page (e.g., "/onetone").
        page_title: The title displayed at the top of the page.
        controller_class: The controller class to use (must inherit from BaseMeasurementController).
        app_state: The global AppState object.
        state_attr: The attribute name in AppState for the page's persistent state (e.g., "onetone_state").
        settings_card_func: The function to render the settings card (e.g., frequency_settings_card).
        settings_card_kwargs: Additional arguments for the settings card function (excluding state, app_state, on_run_callback).
        plot_title: Title for the live plot card.
        fit_plot_title: Title for the fit plot section.
        update_button_text: Text for the update result button.
    """
    
    # Get the persistent state object
    state = getattr(app_state, state_attr)

    @ui.page(page_route)
    def measurement_page():
        controller = controller_class(app_state, state)

        def content():
            ui.label(page_title).classes("text-xl font-semibold mb-4")

            raw_cfg = app_state.current_cfg
            if raw_cfg is None:
                ui.label("No qubit selected").classes("text-red-500")
                return

            # Optional: Auto-update center freq logic could be injected here or handled by controller
            # For now, we leave it to the specific page implementation or controller init if needed.
            # But since it requires raw_cfg, maybe controller.init_state(raw_cfg)?
            # Let's keep it simple for now.

            with ui.row().classes("w-full items-start gap-8"):
                # --- Left Card: Settings ---
                with ui.card().classes("max-w-xs"):
                    # Check if controller has on_settings_change method
                    on_change_callback = getattr(controller, "on_settings_change", None)
                    
                    run_button = settings_card_func(
                        state,
                        app_state,
                        controller.run_measurement,
                        on_change=on_change_callback,
                        **settings_card_kwargs
                    )

                # --- Right Card: Plots ---
                with ui.card().classes("flex-1"):
                    ui.label(plot_title).classes("font-semibold mb-2")
                    
                    progress_bar = ui.linear_progress(value=0).props("instant-feedback").classes("w-full mt-1")
                    progress_info_label = ui.label().classes("text-xs text-gray-500 mb-2")

                    plot_container = ui.column().classes("w-full")
                    last_time_label = ui.label().classes("text-gray-500 text-sm mt-2")
                    
                    ui.separator().classes("my-4")
                    ui.label(fit_plot_title).classes("font-semibold mb-2")
                    fit_plot_container = ui.column().classes("w-full")
                    
                    update_button = ui.button(update_button_text, on_click=controller.update_result).classes("mt-2")
                    update_button.disable()

                    controller.set_ui_elements(
                        plot_container, 
                        fit_plot_container,
                        last_time_label, 
                        progress_bar, 
                        progress_info_label,
                        run_button,
                        update_button
                    )

                    # --- Load Previous Data ---
                    # This logic is common but relies on specific state attribute names (freqs/gains, iq_data/iq_list)
                    # We can try to generalize or let the controller handle it.
                    # Let's try to generalize based on common patterns.
                    
                    x_data = None
                    y_data = None
                    
                    # Try to find x data (freqs or gains)
                    if hasattr(state, "freqs"):
                        x_data = state.freqs
                    elif hasattr(state, "gains"):
                        x_data = state.gains
                    elif hasattr(state, "times"):
                        x_data = state.times
                        
                    # Try to find y data (iq_data or iq_list)
                    if hasattr(state, "iq_data") and state.iq_data is not None:
                        y_data = state.iq_data
                    elif hasattr(state, "iq_list"):
                        iq_list = state.iq_list
                        if iq_list and len(iq_list) > 0 and len(iq_list[0]) > 0:
                             try:
                                y_data = iq_list[0][0].dot([1, 1j])
                             except:
                                pass

                    if x_data is not None and y_data is not None and len(x_data) == len(y_data):
                        with plot_container:
                            with ui.matplotlib(figsize=(9, 4)).figure as fig:
                                ax = fig.gca()
                                ax.plot(x_data, np.abs(y_data), "o-", markersize=4)
                                # Labels could be passed in or guessed
                                ax.set_title(f"{plot_title} (Loaded)")
                        
                        controller.update_fit_plot(x_data, y_data)
                        
                        if hasattr(state, "last_plot_time") and last_time_label:
                            last_time_label.text = "Last shown: " + state.last_plot_time
                    else:
                        with plot_container:
                             ui.label("No valid previous data").classes("text-gray-400 italic")

        page_layout(app_state, content)
