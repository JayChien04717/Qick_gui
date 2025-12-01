from dataclasses import dataclass, field
import numpy as np
from typing import List, Optional  # 確保你引入了這些類型


# 假設你使用了 dataclass
@dataclass
class OneToneState:
    # 掃描模式參數
    sweep_mode: str = "start_stop"
    start_freq: float = 6000.0
    stop_freq: float = 6050.0
    center_freq: float = 5792
    span: float = 30.0

    # 測量參數
    steps: int = 101
    gain: float = 0.3
    py_avg: int = 10

    iq_list: List[list] = field(default_factory=list)

    freqs: Optional[np.ndarray] = None  # 或 field(default_factory=lambda: np.array([]))
    
    fit_results: Optional[dict] = None
    
    last_plot_time: str = ""
