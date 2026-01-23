"""
NovaPulse - GPU Scheduler Controller
Controla Hardware-Accelerated GPU Scheduling e outras opções de GPU
"""
import winreg
import ctypes
import subprocess
from typing import Dict, Optional, Tuple


class GPUSchedulerController:
    """
    Controla configurações avançadas de GPU do Windows
    Inclui HAGS (Hardware-Accelerated GPU Scheduling)
    """
    
    GPU_KEY = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, value_type=winreg.REG_DWORD) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[GPU] Erro no registro: {e}")
            return False
    
    def _get_registry_value(self, key_path: str, value_name: str) -> Optional[any]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def enable_hardware_accelerated_scheduling(self, enable: bool = True) -> bool:
        """
        Habilita/desabilita Hardware-Accelerated GPU Scheduling (HAGS)
        
        HAGS permite que a GPU gerencie sua própria memória de vídeo,
        reduzindo latência e overhead da CPU.
        
        Requisitos:
        - Windows 10 2004+ ou Windows 11
        - GPU com suporte (NVIDIA 1000+, AMD 5000+)
        - Driver atualizado
        """
        if not self.is_admin:
            return False
        
        value = 2 if enable else 1  # 2 = habilitado, 1 = desabilitado
        success = self._set_registry_value(self.GPU_KEY, "HwSchMode", value)
        
        if success:
            state = "habilitado" if enable else "desabilitado"
            print(f"[GPU] ✓ Hardware-Accelerated Scheduling {state}")
            print("[GPU] ⚠ Reinicie o PC para aplicar")
            self.applied_changes['hags'] = enable
        
        return success
    
    def set_gpu_priority(self, priority: int = 8) -> bool:
        """
        Define prioridade de GPU no sistema (0-8)
        8 = Máxima prioridade para GPU
        """
        if not self.is_admin:
            return False
        
        priority = max(0, min(8, priority))
        
        # Define em MMCSS também
        mmcss_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        success = self._set_registry_value(mmcss_key, "GPUPriority", priority)
        
        if success:
            print(f"[GPU] ✓ GPU Priority = {priority}")
            self.applied_changes['priority'] = priority
        
        return success
    
    def optimize_dxgi(self) -> bool:
        """
        Otimiza DXGI (DirectX Graphics Infrastructure)
        Reduz latência de apresentação de frames
        """
        if not self.is_admin:
            return False
        
        try:
            # TdrLevel - Timeout Detection and Recovery
            # 0 = Desativado (não recomendado)
            # 3 = Recovery padrão
            success = self._set_registry_value(self.GPU_KEY, "TdrLevel", 3)
            
            # TdrDelay - Tempo antes de considerar GPU travada
            success2 = self._set_registry_value(self.GPU_KEY, "TdrDelay", 10)
            
            if success and success2:
                print("[GPU] ✓ DXGI/TDR otimizado")
                self.applied_changes['dxgi'] = True
                return True
                
        except Exception as e:
            print(f"[GPU] ✗ Erro ao otimizar DXGI: {e}")
        
        return False
    
    def disable_fullscreen_optimizations_globally(self) -> bool:
        """
        Desativa Fullscreen Optimizations globalmente
        (Também pode ser feito por aplicativo)
        """
        if not self.is_admin:
            return False
        
        try:
            compat_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
            # Nota: Isso define para novos apps, apps existentes precisam de configuração individual
            print("[GPU] ℹ Fullscreen Optimizations devem ser desativadas por app")
            print("[GPU] ℹ Clique direito no .exe > Propriedades > Compatibilidade")
            self.applied_changes['fso'] = True
            return True
        except:
            return False
    
    def enable_game_mode(self) -> bool:
        """
        Habilita Game Mode do Windows
        """
        if not self.is_admin:
            return False
        
        try:
            game_key = r"SOFTWARE\Microsoft\GameBar"
            # AutoGameModeEnabled = 1
            success = self._set_registry_value(game_key, "AutoGameModeEnabled", 1)
            
            if success:
                print("[GPU] ✓ Game Mode habilitado")
                self.applied_changes['game_mode'] = True
            
            return success
        except:
            return False
    
    def set_preferred_gpu_high_performance(self) -> bool:
        """
        Define GPU preferida para alto desempenho (para laptops com GPU integrada + dedicada)
        """
        if not self.is_admin:
            return False
        
        try:
            # GpuPreference: 0 = Auto, 1 = Power Saving, 2 = High Performance
            preference_key = r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences"
            
            # Define globalmente que apps devem usar GPU de alta performance
            print("[GPU] ℹ GPU preference deve ser definida em Configurações > Sistema > Tela")
            print("[GPU] ℹ Ou por aplicativo nas Configurações de Gráficos")
            return True
        except:
            return False
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """
        Aplica todas as otimizações de GPU
        """
        print("\n[GPU] Aplicando otimizações de GPU Scheduler...")
        
        results = {}
        results['hags'] = self.enable_hardware_accelerated_scheduling(True)
        results['priority'] = self.set_gpu_priority(8)
        results['dxgi'] = self.optimize_dxgi()
        results['game_mode'] = self.enable_game_mode()
        
        success_count = sum(results.values())
        print(f"[GPU] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        if results['hags']:
            print("[GPU] ⚠ REINÍCIO NECESSÁRIO para Hardware-Accelerated Scheduling")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status atual das configurações de GPU"""
        status = {}
        
        hags = self._get_registry_value(self.GPU_KEY, "HwSchMode")
        status['hags'] = "Habilitado" if hags == 2 else "Desabilitado" if hags == 1 else "Não definido"
        
        tdr_level = self._get_registry_value(self.GPU_KEY, "TdrLevel")
        status['tdr_level'] = tdr_level
        
        return status
    
    def check_gpu_support(self) -> Tuple[bool, str]:
        """Verifica se a GPU suporta HAGS"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            
            # NVIDIA 1000+ series suporta HAGS
            supported = any(x in name.upper() for x in ['GTX 10', 'GTX 16', 'RTX'])
            return supported, name
        except:
            return False, "GPU não detectada"


# Singleton
_instance = None

def get_controller() -> GPUSchedulerController:
    global _instance
    if _instance is None:
        _instance = GPUSchedulerController()
    return _instance


if __name__ == "__main__":
    controller = GPUSchedulerController()
    print("Status atual:", controller.get_status())
    supported, gpu_name = controller.check_gpu_support()
    print(f"GPU: {gpu_name}")
    print(f"HAGS Suportado: {supported}")
