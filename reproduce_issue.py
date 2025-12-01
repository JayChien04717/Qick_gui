from addict import Dict
import copy

try:
    d = Dict()
    d.a = 1
    d.b = {"c": 2}
    print("Created addict.Dict:", d)
    
    print("Attempting deepcopy...")
    d_copy = copy.deepcopy(d)
    print("Deepcopy successful:", d_copy)
    
except Exception as e:
    print(f"Deepcopy failed: {e}")
    import traceback
    traceback.print_exc()
