"""
Centralized Temperature Service
Single source of truth for CPU/GPU temperature readings with caching
"""
import time
import threading

class TemperatureService:
    """Thread-safe temperature service with caching"""
    
    def __init__(self, cache_ttl=2.0):
        self.cache_ttl = cache_ttl  # Seconds
        self._cache = {}
        self._lock = threading.Lock()
        
        # Try to initialize WMI connection once
        self._wmi_thermal = None
        self._wmi_ohw = None
        self._init_wmi()
        
        # NVIDIA handle
        self._nvidia_handle = None
        self._init_nvidia()
    
    def _init_wmi(self):
        """Initialize WMI connections (once)"""
        try:
            import wmi
            # Primary: ACPI Thermal Zone
            self._wmi_thermal = wmi.WMI(namespace="root\\wmi")
        except:
            pass
            
        try:
            import wmi
            # Fallback: OpenHardwareMonitor/LibreHardwareMonitor
            self._wmi_ohw = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        except:
            pass
    
    def _init_nvidia(self):
        """Initialize NVIDIA handle (once)"""
        try:
            import pynvml
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                self._nvidia_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        except:
            pass
    
    def _get_cached(self, key):
        """Get cached value if still valid"""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return value
        return None
    
    def _set_cached(self, key, value):
        """Set cached value"""
        with self._lock:
            self._cache[key] = (value, time.time())
    
    def get_cpu_temp(self) -> float:
        """Get CPU temperature (cached)"""
        cached = self._get_cached('cpu_temp')
        if cached is not None:
            return cached
        
        temp = 0.0
        
        # Method 1: OpenHardwareMonitor / LibreHardwareMonitor (mais preciso)
        if self._wmi_ohw:
            try:
                for sensor in self._wmi_ohw.Sensor():
                    if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                        temp = float(sensor.Value)
                        break
            except:
                pass
        
        # Method 2: WMI ACPI Thermal Zone (menos preciso)
        if temp == 0 and self._wmi_thermal:
            try:
                t_info = self._wmi_thermal.MSAcpi_ThermalZoneTemperature()[0]
                acpi_temp = (t_info.CurrentTemperature / 10.0) - 273.15
                # ACPI é temperatura da zona térmica, não do die do CPU
                # Em laptops, o die é ~15-20°C mais quente que a zona
                temp = acpi_temp + 20
            except:
                pass
        
        # Method 3: Estimar baseado na GPU (laptop compartilha cooler)
        if temp == 0 or temp < 40:  # Se temp ainda parece baixa demais
            gpu_temp = self.get_gpu_temp()
            if gpu_temp > 0:
                # Em laptops com cooling compartilhado, CPU ~10°C mais quente que GPU
                estimated = gpu_temp + 10
                # Usa o maior valor entre ACPI corrigido e estimativa GPU
                temp = max(temp, estimated)
        
        self._set_cached('cpu_temp', temp)
        return temp
    
    def get_gpu_temp(self) -> float:
        """Get NVIDIA GPU temperature (cached)"""
        cached = self._get_cached('gpu_temp')
        if cached is not None:
            return cached
        
        temp = 0.0
        
        if self._nvidia_handle:
            try:
                import pynvml
                temp = float(pynvml.nvmlDeviceGetTemperature(self._nvidia_handle, 0))
            except:
                pass
        
        self._set_cached('gpu_temp', temp)
        return temp


# Global singleton instance
_instance = None

def get_service() -> TemperatureService:
    """Get singleton instance of TemperatureService"""
    global _instance
    if _instance is None:
        _instance = TemperatureService(cache_ttl=2.0)
    return _instance
