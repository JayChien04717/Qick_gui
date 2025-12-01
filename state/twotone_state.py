from dataclasses import dataclass, field
import numpy as np
from typing import List, Optional  # 確保你引入了這些類型


# 假設你使用了 dataclass
@dataclass
class TwoToneState:
    # 掃描模式參數
    sweep_mode: str = "start_stop"
    start_freq: float = 4000
    stop_freq: float = 5000
    center_freq: float = 4049.8
    span: float = 50

    # 測量參數
    steps: int = 101
    gain: float = 0.3
    py_avg: int = 20
    probe_len: float = 2.0

    iq_list: List[list] = field(default_factory=list)

    freqs: Optional[np.ndarray] = None  # 或 field(default_factory=lambda: np.array([]))
    iq_data: Optional[np.ndarray] = None # Added for storing complex data
    fit_results: Optional[dict] = None # Added for storing fit results

    last_plot_time: str = ""
