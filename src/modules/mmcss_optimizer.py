"""
NovaPulse - MMCSS Optimizer
Otimiza Multimedia Class Scheduler Service para melhor áudio/vídeo
"""
import winreg
import ctypes
from typing import Dict, Optional


class MMCSSOptimizer:
    """
    Otimiza o Multimedia Class Scheduler Service (MMCSS)
    MMCSS gerencia prioridade de threads de mídia (áudio, vídeo, jogos)
    """
    
    MMCSS_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    TASKS_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, value_type=winreg.REG_DWORD) -> bool:
        """Define valor no registro"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[MMCSS] Erro no registro: {e}")
            return False
    
    def _get_registry_value(self, key_path: str, value_name: str) -> Optional[any]:
        """Obtém valor do registro"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def set_system_responsiveness(self, value: int = 0) -> bool:
        """
        Define responsividade do sistema (0-100)
        0 = Prioridade máxima para mídia (pode afetar outras tarefas)
        10 = Gaming recomendado (bom balanço)
        20 = Padrão Windows
        """
        if not self.is_admin:
            return False
        
        value = max(0, min(100, value))
        success = self._set_registry_value(self.MMCSS_KEY, "SystemResponsiveness", value)
        
        if success:
            print(f"[MMCSS] ✓ SystemResponsiveness = {value}")
            self.applied_changes['responsiveness'] = value
        
        return success
    
    def disable_network_throttling(self) -> bool:
        """
        Desativa throttling de rede durante reprodução de mídia
        Impacto: Melhor streaming, menos buffering
        """
        if not self.is_admin:
            return False
        
        # NetworkThrottlingIndex = FFFFFFFF (desativado)
        success = self._set_registry_value(self.MMCSS_KEY, "NetworkThrottlingIndex", 0xFFFFFFFF)
        
        if success:
            print("[MMCSS] ✓ Network Throttling desativado")
            self.applied_changes['network_throttling'] = False
        
        return success
    
    def optimize_gaming_task(self) -> bool:
        """
        Otimiza configurações do task 'Games'
        """
        if not self.is_admin:
            return False
        
        games_key = f"{self.TASKS_KEY}\\Games"
        
        try:
            # Abre ou cria a chave Games
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, games_key, 0, winreg.KEY_SET_VALUE)
            
            # Configurações otimizadas para gaming
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)  # Todos os cores
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)  # 1ms
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)  # Máximo
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)  # High
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Games' otimizado")
            self.applied_changes['games_task'] = True
            return True
            
        except Exception as e:
            print(f"[MMCSS] ✗ Erro ao otimizar Games task: {e}")
            return False
    
    def optimize_audio_task(self) -> bool:
        """
        Otimiza configurações do task 'Audio'
        """
        if not self.is_admin:
            return False
        
        audio_key = f"{self.TASKS_KEY}\\Audio"
        
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, audio_key, 0, winreg.KEY_SET_VALUE)
            
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "True")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Audio' otimizado")
            self.applied_changes['audio_task'] = True
            return True
            
        except Exception as e:
            print(f"[MMCSS] ✗ Erro ao otimizar Audio task: {e}")
            return False
    
    def optimize_pro_audio_task(self) -> bool:
        """
        Otimiza configurações do task 'Pro Audio' (DAWs, produção musical)
        """
        if not self.is_admin:
            return False
        
        proaudio_key = f"{self.TASKS_KEY}\\Pro Audio"
        
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, proaudio_key, 0, winreg.KEY_SET_VALUE)
            
            winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
            winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 8)  # Critical
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            
            winreg.CloseKey(key)
            print("[MMCSS] ✓ Task 'Pro Audio' otimizado")
            self.applied_changes['proaudio_task'] = True
            return True
            
        except Exception as e:
            print(f"[MMCSS] ✗ Erro ao otimizar Pro Audio task: {e}")
            return False
    
    def apply_all_optimizations(self, gaming_focused: bool = True) -> Dict[str, bool]:
        """
        Aplica todas as otimizações MMCSS
        gaming_focused: Prioriza gaming sobre outras mídias
        """
        print("\n[MMCSS] Aplicando otimizações de Multimedia Scheduler...")
        
        results = {}
        
        # Responsividade: 0 para gaming máximo, 10 para balance
        responsiveness = 0 if gaming_focused else 10
        results['responsiveness'] = self.set_system_responsiveness(responsiveness)
        results['network_throttling'] = self.disable_network_throttling()
        results['games_task'] = self.optimize_gaming_task()
        results['audio_task'] = self.optimize_audio_task()
        results['proaudio_task'] = self.optimize_pro_audio_task()
        
        success_count = sum(results.values())
        print(f"[MMCSS] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status atual das configurações MMCSS"""
        status = {}
        
        status['responsiveness'] = self._get_registry_value(self.MMCSS_KEY, "SystemResponsiveness")
        status['network_throttling'] = self._get_registry_value(self.MMCSS_KEY, "NetworkThrottlingIndex")
        
        return status


# Singleton
_instance = None

def get_optimizer() -> MMCSSOptimizer:
    global _instance
    if _instance is None:
        _instance = MMCSSOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = MMCSSOptimizer()
    print("Status atual:", optimizer.get_status())
    # optimizer.apply_all_optimizations()
