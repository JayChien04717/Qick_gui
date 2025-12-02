# QICK Instrument Control GUI

A modern, web-based graphical user interface for the QICK (Quantum Instrumentation Control Kit) system, built with [NiceGUI](https://nicegui.io/).

## Features

*   **Web-Based Interface**: Accessible via browser, enabling remote control and monitoring.
*   **QICK Integration**: Seamless connection to QICK boards via Pyro4.
*   **Measurement Modules**:
    *   **One Tone Spectroscopy**: Resonator spectroscopy.
    *   **Two Tone Spectroscopy**: Qubit spectroscopy.
    *   **Power Rabi**: Rabi oscillation measurement.
    *   **Ramsey**: T2* measurement.
    *   **Spin Echo**: T2 measurement.
    *   **T1**: Relaxation time measurement.
    *   **Single Shot**: Readout fidelity measurement.
*   **Dynamic Configuration**: Real-time update of instrument parameters via a sidebar.
*   **Live Plotting**: Real-time visualization of measurement data.
*   **Remote Access**: Integrated Ngrok support for secure remote access.
*   **Authentication**: Simple login system to protect the control interface.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd inst_control
    ```

2.  **Create a Conda environment** (recommended):
    ```bash
    conda create -n qick2env python=3.9
    conda activate qick2env
    ```

3.  **Install dependencies**:
    ```bash
    pip install nicegui pyngrok pyro4 matplotlib numpy scipy tqdm addict
    # Ensure qick library is installed (usually from local source or specific repo)
    ```

## Usage

1.  **Start the Application**:
    ```bash
    python main.py
    ```

2.  **Access the GUI**:
    *   **Local**: Open `http://localhost:8081` in your browser.
    *   **Remote**: The terminal will display an Ngrok URL (e.g., `https://xxxx.ngrok-free.dev`).

3.  **Login**:
    *   **Default Account**: `SQC`
    *   **Default Password**: `test`
    *   *(Note: Credentials can be modified in `pages/login.py`)*

4.  **Connect to QICK**:
    *   Go to the **Connect** page.
    *   Enter the IP address and Port of your QICK board.
    *   Click **Connect**.

5.  **Run Measurements**:
    *   Select a measurement from the sidebar (e.g., One Tone).
    *   Configure parameters (Frequency, Gain, etc.).
    *   Click **Run Measurement**.

## Project Structure

```
inst_control/
├── main.py                 # Entry point, app initialization, Ngrok setup
├── layout/
│   ├── layout.py           # Main page layout, navigation, auth check
│   ├── sidebar.py          # Configuration sidebar
│   ├── base_page.py        # Base class for measurement pages
│   ├── measurement_tools.py# Helper functions for measurements
│   ├── nicegui_plot.py     # Plotting utilities
│   └── sweep_ui.py         # UI components for sweep settings
├── pages/
│   ├── login.py            # Login page
│   ├── connect.py          # Connection page
│   ├── onetone.py          # One Tone measurement
│   ├── twotone.py          # Two Tone measurement
│   ├── prabi.py            # Power Rabi measurement
│   ├── ramsey.py           # Ramsey measurement
│   ├── spinecho.py         # Spin Echo measurement
│   ├── t1.py               # T1 measurement
│   └── singleshot.py       # Single Shot measurement
├── state/                  # State management (Dataclasses)
│   ├── app_state.py        # Global application state
│   └── ... (individual measurement states)
└── qick_workspace/         # QICK programs and scripts
```

## Configuration

*   **Ngrok**: The Ngrok auth token is configured in `main.py`.
*   **Users**: User accounts are defined in `pages/login.py`.
*   **QICK Config**: The app reads QICK configuration files (JSON) via the `qick_workspace` tools.

## License

[MIT License](LICENSE)
