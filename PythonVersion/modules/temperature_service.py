"""
Centralized Temperature Service v2.0
Multiple methods for CPU/GPU temperature reading with fallbacks
"""
import time
import threading
import subprocess

class TemperatureService:
    """Thread-safe temperature service with multiple reading methods"""
    
    def __init__(self, cache_ttl=2.0):
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._lock = threading.Lock()
        
        # WMI connections
        self._wmi_thermal = None
        self._wmi_ohw = None
        self._wmi_root = None
        self._init_wmi()
        
        # NVIDIA handle
        self._nvidia_handle = None
        self._init_nvidia()
    
    def _init_wmi(self):
        """Initialize WMI connections"""
        try:
            import wmi
            self._wmi_root = wmi.WMI()
        except:
            pass
            
        try:
            import wmi
            self._wmi_thermal = wmi.WMI(namespace="root\\wmi")
        except:
            pass
            
        try:
            import wmi
            self._wmi_ohw = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        except:
            try:
                import wmi
                self._wmi_ohw = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            except:
                pass
    
    def _init_nvidia(self):
        """Initialize NVIDIA handle"""
        try:
            import pynvml
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                self._nvidia_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        except:
            pass
    
    def _get_cached(self, key):
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return value
        return None
    
    def _set_cached(self, key, value):
        with self._lock:
            self._cache[key] = (value, time.time())
    
    def get_cpu_temp(self) -> float:
        """Get CPU temperature using multiple methods"""
        cached = self._get_cached('cpu_temp')
        if cached is not None:
            return cached
        
        temp = 0.0
        
        # Method 1: OpenHardwareMonitor / LibreHardwareMonitor (most accurate)
        if temp == 0 and self._wmi_ohw:
            try:
                for sensor in self._wmi_ohw.Sensor():
                    if sensor.SensorType == 'Temperature':
                        name = sensor.Name.lower()
                        if 'cpu' in name or 'core' in name or 'package' in name:
                            temp = float(sensor.Value)
                            if temp > 0:
                                break
            except:
                pass
        
        # Method 2: WMI Win32_TemperatureProbe (some systems)
        if temp == 0 and self._wmi_root:
            try:
                for probe in self._wmi_root.Win32_TemperatureProbe():
                    if probe.CurrentReading:
                        temp = float(probe.CurrentReading) / 10.0
                        if temp > 0:
                            break
            except:
                pass
        
        # Method 3: ACPI Thermal Zone
        if temp == 0 and self._wmi_thermal:
            try:
                zones = self._wmi_thermal.MSAcpi_ThermalZoneTemperature()
                if zones:
                    # Get max temperature from all zones
                    max_temp = 0
                    for zone in zones:
                        zone_temp = (zone.CurrentTemperature / 10.0) - 273.15
                        if zone_temp > max_temp:
                            max_temp = zone_temp
                    if max_temp > 0:
                        # ACPI zone is chassis temp, CPU die ~15-25°C higher
                        temp = max_temp + 20
            except:
                pass
        
        # Method 4: Use NVIDIA GPU as reference (laptops share cooling)
        if temp == 0 or temp < 35:
            gpu_temp = self.get_gpu_temp()
            if gpu_temp > 0:
                # CPU usually runs 5-15°C hotter than GPU in laptops
                estimated = gpu_temp + 12
                temp = max(temp, estimated) if temp > 0 else estimated
        
        # Method 5: Use Intel GPU temp if available
        if temp == 0 or temp < 35:
            intel_temp = self.get_intel_gpu_temp()
            if intel_temp > 0:
                # Intel iGPU is on the same die as CPU, similar temp
                temp = max(temp, intel_temp + 5) if temp > 0 else intel_temp + 5
        
        # Sanity check
        if temp > 120 or temp < 0:
            temp = 0
        
        self._set_cached('cpu_temp', temp)
        return temp
    
    def get_gpu_temp(self) -> float:
        """Get NVIDIA GPU temperature"""
        cached = self._get_cached('gpu_temp')
        if cached is not None:
            return cached
        
        temp = 0.0
        
        # NVIDIA via pynvml
        if self._nvidia_handle:
            try:
                import pynvml
                temp = float(pynvml.nvmlDeviceGetTemperature(self._nvidia_handle, 0))
            except:
                pass
        
        # Fallback: OpenHardwareMonitor
        if temp == 0 and self._wmi_ohw:
            try:
                for sensor in self._wmi_ohw.Sensor():
                    if sensor.SensorType == 'Temperature':
                        name = sensor.Name.lower()
                        if 'gpu' in name and 'nvidia' in sensor.Parent.lower():
                            temp = float(sensor.Value)
                            break
            except:
                pass
        
        self._set_cached('gpu_temp', temp)
        return temp
    
    def get_intel_gpu_temp(self) -> float:
        """Get Intel integrated GPU temperature"""
        cached = self._get_cached('intel_gpu_temp')
        if cached is not None:
            return cached
        
        temp = 0.0
        
        # Try OpenHardwareMonitor
        if self._wmi_ohw:
            try:
                for sensor in self._wmi_ohw.Sensor():
                    if sensor.SensorType == 'Temperature':
                        name = sensor.Name.lower()
                        parent = sensor.Parent.lower() if hasattr(sensor, 'Parent') else ""
                        if 'intel' in parent or 'iris' in name or 'uhd' in name:
                            temp = float(sensor.Value)
                            if temp > 0:
                                break
            except:
                pass
        
        self._set_cached('intel_gpu_temp', temp)
        return temp
    
    def get_all_temperatures(self) -> dict:
        """Get all available temperatures"""
        return {
            'cpu': self.get_cpu_temp(),
            'gpu_nvidia': self.get_gpu_temp(),
            'gpu_intel': self.get_intel_gpu_temp()
        }


# Global singleton
_instance = None

def get_service() -> TemperatureService:
    """Get singleton instance"""
    global _instance
    if _instance is None:
        _instance = TemperatureService(cache_ttl=2.0)
    return _instance
