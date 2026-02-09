"""
Timer Resolution Optimizer
Forces timer resolution to 0.5ms (better input lag)
"""
import ctypes
import threading
import time

class TimerResolutionOptimizer:
    """Optimizes Windows timer resolution for low latency"""
    
    def __init__(self):
        self.ntdll = ctypes.WinDLL('ntdll')
        self.running = False
        self.thread = None
        self.original_resolution = None
        
        # Target: 0.5ms (5000 * 100ns = 0.5ms)
        self.target_resolution = 5000  # 100-nanosecond units
    
    def get_current_resolution(self):
        """Returns current timer resolution in ms"""
        try:
            current = ctypes.c_ulong()
            minimum = ctypes.c_ulong()
            maximum = ctypes.c_ulong()
            
            self.ntdll.NtQueryTimerResolution(
                ctypes.byref(minimum),
                ctypes.byref(maximum),
                ctypes.byref(current)
            )
            
            return current.value / 10000  # Convert to ms
        except:
            return 15.625  # Default Windows
    
    def set_resolution(self, resolution_100ns):
        """Set timer resolution (in 100ns units)"""
        try:
            actual = ctypes.c_ulong()
            
            # NtSetTimerResolution(DesiredResolution, SetResolution, ActualResolution)
            result = self.ntdll.NtSetTimerResolution(
                ctypes.c_ulong(resolution_100ns),
                ctypes.c_bool(True),
                ctypes.byref(actual)
            )
            
            if result == 0:  # STATUS_SUCCESS
                return actual.value / 10000  # Return in ms
            return None
        except Exception as e:
            print(f"[TIMER] Error: {e}")
            return None
    
    def apply_optimization(self):
        """Apply timer optimization (0.5ms)"""
        print("[TIMER] Applying timer resolution to 0.5ms...")
        
        # Save original resolution
        self.original_resolution = self.get_current_resolution()
        print(f"[TIMER] Original resolution: {self.original_resolution:.3f}ms")
        
        # Apply new resolution
        actual = self.set_resolution(self.target_resolution)
        
        if actual:
            print(f"[TIMER] ✓ New resolution: {actual:.3f}ms")
            print(f"[TIMER] ✓ Improvement: -{(self.original_resolution - actual):.2f}ms input lag")
            return True
        else:
            print("[TIMER] ⚠ Could not change resolution")
            return False
    
    def start_persistent(self):
        """Keep resolution low persistently (some apps reset it)"""
        self.running = True
        
        def maintain_loop():
            while self.running:
                self.set_resolution(self.target_resolution)
                time.sleep(60)  # Re-apply every 60 seconds
        
        self.thread = threading.Thread(target=maintain_loop, daemon=True)
        self.thread.start()
    
    def restore(self):
        """Restore default resolution"""
        self.running = False
        if self.original_resolution:
            # 156250 = 15.625ms (Windows default)
            self.set_resolution(156250)
            print("[TIMER] Resolution restored to default")


if __name__ == "__main__":
    timer = TimerResolutionOptimizer()
    print(f"Current resolution: {timer.get_current_resolution():.3f}ms")
    
    timer.apply_optimization()
    
    input("Press ENTER to restore...")
    timer.restore()
