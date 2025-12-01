import sys
import os
import copy
import traceback

# Add project root to path
sys.path.append(os.getcwd())

from qick_workspace.tools.system_tool import ExperimentConfig
from qick_workspace.tools.ncfg import config_list

try:
    print("Initializing ExperimentConfig...")
    qick_cfg = ExperimentConfig(config_list)
    
    print("Getting qubit Q1...")
    current_cfg = qick_cfg.get_qubit("Q1")
    print(f"Got config of type: {type(current_cfg)}")
    
    print("Attempting deepcopy...")
    config_copy = copy.deepcopy(current_cfg)
    print("Deepcopy successful!")
    
except Exception as e:
    print(f"Deepcopy failed: {e}")
    traceback.print_exc()
