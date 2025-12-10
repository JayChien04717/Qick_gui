from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class SingleshotOptState:
    """State for Single Shot Optimize measurement."""
    
    # Sweep parameters
    freq_center: float = 0.0  # Will be set from config
    freq_span: float = 10.0  # ±5 MHz
    freq_steps: int = 11
    
    gain_start: float = 0.05
    gain_stop: float = 0.4
    gain_steps: int = 7
    
    length_start: float = 0.1  # us
    length_stop: float = 0.3  # us
    length_steps: int = 7
    
    # Sweep enable flags
    sweep_freq: bool = True
    sweep_gain: bool = True
    sweep_length: bool = True
    
    shot_num: int = 1000
    
    # Results
    opt_freq: Optional[float] = None
    opt_gain: Optional[float] = None
    opt_length: Optional[float] = None
    max_fidelity: Optional[float] = None
    
    fid_array: Optional[np.ndarray] = None
    raw_data: Optional[dict] = None
    
    last_plot_time: str = ""
