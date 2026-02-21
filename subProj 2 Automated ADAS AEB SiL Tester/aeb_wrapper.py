import ctypes
import os

class AEBSystem:
    """ Python Wrapper for the C++ AEB logic module """
    def __init__(self):
        # Load the shared library
        lib_path = os.path.join(os.path.dirname(__file__), 'aeb_lib.so')
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Shared library not found at {lib_path}. Run 'make' first.")
        
        self.lib = ctypes.CDLL(lib_path)
        
        # Define argument and return types to ensure type safety bridging C++ and Python
        self.lib.calculate_braking_force.argtypes = (ctypes.c_double, ctypes.c_double, ctypes.c_double)
        self.lib.calculate_braking_force.restype = ctypes.c_int

    def evaluate(self, ego_speed: float, obj_distance: float, speed_relative: float) -> int:
        """
        Evaluate AEB scenario and return required braking force (0-100%).
        """
        return self.lib.calculate_braking_force(ego_speed, obj_distance, speed_relative)
