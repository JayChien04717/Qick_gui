from dataclasses import dataclass, field
import numpy as np
from typing import List, Optional

@dataclass
class SingleshotState:
    # Measurement Parameters
    shot_num: int = 5000
    
    # Data Storage
    iq_list: List[list] = field(default_factory=list)
    iq_data: Optional[np.ndarray] = None
    raw_data: Optional[dict] = None # Added for dynamic plotting
    times: Optional[np.ndarray] = None
    
    fid_avg: Optional[bool] = False 
    fit: Optional[bool] = False
    gauss_overlap: Optional[bool] = False  
    plotoverlap: Optional[bool] = False
    fit_results: Optional[dict] = None
    
    last_plot_time: str = ""
