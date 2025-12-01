from dataclasses import dataclass, field
import numpy as np
from typing import List, Optional

@dataclass
class T1State:
    # Sweep Parameters
    start_time: float = 0.0
    stop_time: float = 50

    # Measurement Parameters
    steps: int = 101
    py_avg: int = 10
    
    # Data Storage
    iq_list: List[list] = field(default_factory=list)
    iq_data: Optional[np.ndarray] = None
    times: Optional[np.ndarray] = None
    
    fit_results: Optional[dict] = None
    
    last_plot_time: str = ""
