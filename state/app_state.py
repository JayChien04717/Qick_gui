# state/app_state.py
from dataclasses import dataclass, field
from typing import Optional, Any, List, Callable
from qick_workspace.tools.ncfg import config_list
from qick_workspace.tools.system_tool import ExperimentConfig as QickExperimentConfig
from state.onetone_state import OneToneState
from state.twotone_state import TwoToneState
from state.prabi_state import PowerRabiState
from state.ramsey_state import RamseyState
from state.spinecho_state import SpinEchoState
from state.t1_state import T1State
from state.singleshot_state import SingleshotState
from state.singleshot_opt_state import SingleshotOptState


@dataclass
class AppState:
    # ---- Connect status ----
    instrument_ip: str = "192.168.10.63"
    instrument_port: int = 8887
    proxy_name: str = "myqick"
    instrument_connected: bool = False

    # ---- QICK proxy object ----
    soc: Optional[Any] = None
    soccfg: Optional[Any] = None

    # ---- Config system ----
    qubit_names: List[str] = field(default_factory=list)
    qick_cfg: Optional[QickExperimentConfig] = None
    selected_qubit: Optional[str] = None
    current_cfg: Optional[dict] = None
    
    # ---- Persistent Page States ----
    onetone_state: OneToneState = field(default_factory=OneToneState)
    twotone_state: TwoToneState = field(default_factory=TwoToneState)
    prabi_state: PowerRabiState = field(default_factory=PowerRabiState)
    ramsey_state: RamseyState = field(default_factory=RamseyState)
    spinecho_state: SpinEchoState = field(default_factory=SpinEchoState)
    t1_state: T1State = field(default_factory=T1State)
    singleshot_state: SingleshotState = field(default_factory=SingleshotState)
    singleshot_opt_state: SingleshotOptState = field(default_factory=SingleshotOptState)
    
    # ---- UI Callbacks ----
    sidebar_refresh: Optional[Callable] = None

    def __post_init__(self):
        """init qubit config system (dataclass constructor)"""

        self.qubit_names = [c["name"] for c in config_list]

        self.qick_cfg = QickExperimentConfig(config_list)

        self.selected_qubit = self.qubit_names[0]

        self.current_cfg = self.qick_cfg.get_qubit(self.selected_qubit)
        self.view_cfg = self.qick_cfg.read_config(self.selected_qubit)

    def read_config(self, name: str):
        """return read_config result dict"""
        return self.qick_cfg.read_config(name)

    def get_qubit(self, name: str):
        """return get_qubit result QickConfig object"""
        return self.qick_cfg.get_qubit(name)
