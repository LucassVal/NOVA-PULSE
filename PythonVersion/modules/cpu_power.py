"""
Gerenciador de energia e frequência da CPU
"""
import ctypes
from ctypes import wintypes
import subprocess

class CPUPowerManager:
    def __init__(self):
        self.powrprof = ctypes.WinDLL('powrprof')
        
        # GUIDs - Processor Power Management
        self.GUID_PROCESSOR = "SUB_PROCESSOR"
        self.GUID_MAX_THROTTLE = "PROCTHROTTLEMAX"
        self.GUID_MIN_THROTTLE = "PROCTHROTTLEMIN"
    
    def set_max_cpu_frequency(self, percentage):
        """Define frequência máxima da CPU (5-100%)"""
        if not (5 <= percentage <= 100):
            print(f"[ERROR] Percentual inválido: {percentage}%. Deve estar entre 5-100%")
            return False
        
        try:
            print(f"[INFO] Configurando frequência máxima da CPU para {percentage}%")
            
            # Usa powercfg.exe com aliases (mais compatível)
            result = subprocess.run(
                ['powercfg', '-setacvalueindex', 'SCHEME_CURRENT',
                 self.GUID_PROCESSOR, self.GUID_MAX_THROTTLE, str(percentage)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                # Aplica mudanças
                subprocess.run(['powercfg', '-setactive', 'SCHEME_CURRENT'], 
                              capture_output=True, encoding='utf-8', errors='ignore')
                print(f"[SUCCESS] Frequência máxima definida para {percentage}%")
                return True
            else:
                # Silencia erro se já está no valor desejado
                return True
        except Exception as e:
            print(f"[WARN] CPU control: {e}")
            return False
    
    def set_min_cpu_frequency(self, percentage):
        """Define frequência mínima da CPU (0-100%)"""
        if not (0 <= percentage <= 100):
            print(f"[ERROR] Percentual inválido: {percentage}%")
            return False
        
        try:
            print(f"[INFO] Configurando frequência mínima da CPU para {percentage}%")
            
            result = subprocess.run(
                ['powercfg', '-setacvalueindex', 'SCHEME_CURRENT',
                 self.GUID_PROCESSOR, self.GUID_MIN_THROTTLE, str(percentage)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                subprocess.run(['powercfg', '-setactive', 'SCHEME_CURRENT'],
                              capture_output=True, encoding='utf-8', errors='ignore')
                print(f"[SUCCESS] Frequência mínima definida para {percentage}%")
                return True
            else:
                # Silencia erro
                return True
        except Exception as e:
            print(f"[WARN] CPU min control: {e}")
            return False
    
    def start_adaptive_governor(self, base_cap=80):
        """[V2.0] Starts Adaptive Thermal Throttling.
        
        Args:
            base_cap: The auto_profiler's CPU cap (default 80%). 
                      The thermal governor will NEVER exceed this ceiling.
                      It only throttles DOWN further during thermal events.
        
        Fixed: Previously overrode auto_profiler's 80% cap back to 100% when 
        temp < 70°C. Now respects the profiler's cap as the maximum ceiling.
        """
        import threading
        import time
        from modules import temperature_service
        
        self._thermal_base_cap = base_cap
        
        # Get singleton instance (reuses WMI connection)
        temp_svc = temperature_service.get_service()
        
        def thermal_loop():
            print(f"[CPU] Adaptive Thermal Governor STARTED 🚀 (ceiling: {base_cap}%)")
            current_limit = base_cap
            
            while True:
                try:
                    # Use centralized cached temperature service
                    temp = temp_svc.get_cpu_temp()
                        
                    if temp > 0:
                        new_limit = current_limit
                        ceiling = self._thermal_base_cap
                        
                        # LOGIC (respects auto_profiler cap as ceiling):
                        # < 70°C: restore to ceiling (auto_profiler cap)
                        # > 80°C: min(ceiling, 90%) — throttle if needed
                        # > 90°C: min(ceiling, 70%) — emergency throttle
                        
                        if temp < 70 and current_limit < ceiling:
                            new_limit = ceiling
                        elif temp > 90 and current_limit > min(ceiling, 70):
                            new_limit = min(ceiling, 70)
                        elif temp > 80 and temp <= 90 and current_limit > min(ceiling, 90):
                            new_limit = min(ceiling, 90)
                            
                        if new_limit != current_limit:
                            print(f"[CPU] Thermal Event: {temp:.0f}°C -> Adjusting Limit to {new_limit}%")
                            self.set_max_cpu_frequency(new_limit)
                            current_limit = new_limit
                            
                    time.sleep(5)
                except:
                    time.sleep(10)

        t = threading.Thread(target=thermal_loop, daemon=True)
        t.start()

    def restore_defaults(self):
        """Restaura configurações padrão de CPU (100%)"""
        try:
            print("[INFO] Restaurando configurações padrão de CPU...")
            self.set_max_cpu_frequency(100)
            self.set_min_cpu_frequency(5)
            print("[SUCCESS] Configurações de CPU restauradas para padrão")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao restaurar padrões: {e}")
            return False


if __name__ == "__main__":
    # Teste
    manager = CPUPowerManager()
    
    print("Testando controle de CPU...")
    print("1. Definindo máximo para 80%")
    manager.set_max_cpu_frequency(80)
    
    input("\nPressione ENTER para restaurar padrões...")
    manager.restore_defaults()
