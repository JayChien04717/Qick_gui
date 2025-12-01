from dataclasses import dataclass, field
import numpy as np
from typing import List, Optional

@dataclass
class PowerRabiState:
    # Sweep Parameters
    sweep_mode: str = "start_stop" # Although gain sweep usually is start-stop, keeping structure consistent
    start_gain: float = 0.0
    stop_gain: float = 1.0
    
    # Pulse Parameters
    pulse_type: str = "arb" # "arb" or "flat_top"
    flat_top_len: float = 0.05 # us
    sigma: float = 0.05 # us

    # Measurement Parameters
    steps: int = 101
    py_avg: int = 10
    
    # Data Storage
    iq_list: List[list] = field(default_factory=list)
    gains: Optional[np.ndarray] = None
    iq_data: Optional[np.ndarray] = None
    
    fit_results: Optional[dict] = None
    
    last_plot_time: str = ""
