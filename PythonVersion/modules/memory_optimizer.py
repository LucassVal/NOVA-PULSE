"""
NovaPulse - Memory Optimizer Pro
Otimizações avançadas de memória RAM
"""
import winreg
import ctypes
import subprocess
import os
from typing import Dict, Optional


class MemoryOptimizerPro:
    """
    Otimizações avançadas de gerenciamento de memória do Windows
    
    Inclui:
    - Controle de compressão de memória
    - Superfetch/SysMain
    - Prefetch
    - Working Set optimization
    """
    
    MEMORY_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    PREFETCH_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    
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
            print(f"[MEMORY] Erro no registro: {e}")
            return False
    
    def _get_registry_value(self, key_path: str, value_name: str) -> Optional[any]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except:
            return None
    
    def _run_service_cmd(self, service: str, action: str) -> bool:
        """Para/inicia um serviço do Windows"""
        try:
            result = subprocess.run(
                f"sc {action} {service}",
                shell=True, capture_output=True, text=True
            )
            return result.returncode == 0 or "1062" in result.stderr  # 1062 = already stopped
        except:
            return False
    
    def disable_memory_compression(self) -> bool:
        """
        Desativa compressão de memória do Windows
        
        A compressão de memória usa CPU para comprimir dados na RAM,
        reduzindo uso de memória mas aumentando uso de CPU.
        
        Desativar é recomendado para:
        - PCs com bastante RAM (16GB+)
        - Gaming (reduz stuttering)
        - CPUs mais lentas
        """
        if not self.is_admin:
            return False
        
        try:
            # Desativa via PowerShell
            result = subprocess.run(
                'powershell -Command "Disable-MMAgent -MemoryCompression"',
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("[MEMORY] ✓ Compressão de memória desativada")
                self.applied_changes['compression'] = False
                return True
            else:
                print(f"[MEMORY] ℹ Compressão pode já estar desativada")
                return True
        except Exception as e:
            print(f"[MEMORY] ✗ Erro ao desativar compressão: {e}")
            return False
    
    def enable_memory_compression(self) -> bool:
        """Reativa compressão de memória"""
        if not self.is_admin:
            return False
        
        try:
            subprocess.run(
                'powershell -Command "Enable-MMAgent -MemoryCompression"',
                shell=True, capture_output=True
            )
            print("[MEMORY] ✓ Compressão de memória reativada")
            self.applied_changes['compression'] = True
            return True
        except:
            return False
    
    def configure_superfetch(self, mode: int = 0) -> bool:
        """
        Configura SysMain (antigo Superfetch)
        
        Modes:
        0 = Desativado (melhor para SSDs)
        1 = Apenas para boot
        2 = Apenas para aplicativos
        3 = Boot + Aplicativos (padrão Windows)
        """
        if not self.is_admin:
            return False
        
        success = self._set_registry_value(
            self.PREFETCH_KEY,
            "EnableSuperfetch",
            mode
        )
        
        if mode == 0:
            # Para o serviço também
            self._run_service_cmd("SysMain", "stop")
            subprocess.run(
                'sc config SysMain start= disabled',
                shell=True, capture_output=True
            )
            print("[MEMORY] ✓ SysMain/Superfetch desativado")
        else:
            print(f"[MEMORY] ✓ Superfetch configurado (modo {mode})")
        
        self.applied_changes['superfetch'] = mode
        return success
    
    def configure_prefetch(self, mode: int = 0) -> bool:
        """
        Configura Prefetch
        
        Modes:
        0 = Desativado
        1 = Apenas aplicativos
        2 = Apenas boot
        3 = Boot + Aplicativos (padrão)
        """
        if not self.is_admin:
            return False
        
        success = self._set_registry_value(
            self.PREFETCH_KEY,
            "EnablePrefetcher",
            mode
        )
        
        if success:
            state = "desativado" if mode == 0 else f"modo {mode}"
            print(f"[MEMORY] ✓ Prefetch {state}")
            self.applied_changes['prefetch'] = mode
        
        return success
    
    def optimize_paging(self, disable_executive: bool = True) -> bool:
        """
        Otimiza configurações de paginação
        
        disable_executive: Mantém kernel/drivers na RAM (não pagina para disco)
        Recomendado para PCs com RAM suficiente
        """
        if not self.is_admin:
            return False
        
        value = 1 if disable_executive else 0
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "DisablePagingExecutive",
            value
        )
        
        if success:
            state = "kernel mantido em RAM" if disable_executive else "paginação normal"
            print(f"[MEMORY] ✓ Paginação: {state}")
            self.applied_changes['paging_executive'] = disable_executive
        
        return success
    
    def set_large_system_cache(self, enable: bool = False) -> bool:
        """
        Define uso de cache de sistema grande
        
        enable=True: Prioriza cache de arquivos (servidores)
        enable=False: Prioriza aplicativos (desktop/gaming)
        """
        if not self.is_admin:
            return False
        
        value = 1 if enable else 0
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "LargeSystemCache",
            value
        )
        
        if success:
            mode = "cache" if enable else "aplicativos"
            print(f"[MEMORY] ✓ Prioridade de memória: {mode}")
            self.applied_changes['large_cache'] = enable
        
        return success
    
    def optimize_io_page_lock_limit(self) -> bool:
        """
        Aumenta limite de páginas bloqueadas para I/O
        Melhora performance de disco para workloads intensivos
        """
        if not self.is_admin:
            return False
        
        # Valor em bytes (0 = automático, valores altos = mais RAM para I/O)
        # 512MB = 536870912
        success = self._set_registry_value(
            self.MEMORY_KEY,
            "IoPageLockLimit",
            536870912
        )
        
        if success:
            print("[MEMORY] ✓ IoPageLockLimit otimizado (512MB)")
            self.applied_changes['io_page_lock'] = True
        
        return success
    
    def clear_standby_list(self) -> int:
        """
        Limpa Standby List (memória em cache)
        Retorna quantidade liberada em MB
        """
        try:
            import psutil
            mem_before = psutil.virtual_memory().available
            
            # Usa RAMMap ou comando de sistema
            # Através da API NtSetSystemInformation
            ntdll = ctypes.windll.ntdll
            
            # SystemMemoryListInformation = 80
            # MemoryPurgeStandbyList = 4
            command = ctypes.c_int(4)
            result = ntdll.NtSetSystemInformation(80, ctypes.byref(command), ctypes.sizeof(command))
            
            if result == 0:
                mem_after = psutil.virtual_memory().available
                freed_mb = int((mem_after - mem_before) / (1024 * 1024))
                if freed_mb > 0:
                    print(f"[MEMORY] ✓ Standby List limpa: {freed_mb}MB liberados")
                return max(0, freed_mb)
            
        except Exception as e:
            print(f"[MEMORY] ✗ Erro ao limpar standby: {e}")
        
        return 0
    
    def apply_all_optimizations(self, gaming_mode: bool = True) -> Dict[str, bool]:
        """
        Aplica todas as otimizações de memória
        
        gaming_mode: Otimiza para jogos (desativa caches, prioriza apps)
        """
        print("\n[MEMORY] Aplicando otimizações de memória...")
        
        results = {}
        
        if gaming_mode:
            # Para gaming: desativa tudo que compete por RAM
            results['compression'] = self.disable_memory_compression()
            results['superfetch'] = self.configure_superfetch(0)  # Desativado
            results['prefetch'] = self.configure_prefetch(0)  # Desativado
            results['paging'] = self.optimize_paging(disable_executive=True)
            results['cache'] = self.set_large_system_cache(enable=False)
            results['io_lock'] = self.optimize_io_page_lock_limit()
        else:
            # Para uso geral: balanço
            results['compression'] = self.disable_memory_compression()  # Ainda desativa para CPUs
            results['superfetch'] = self.configure_superfetch(3)  # Mantém para HDDs
            results['prefetch'] = self.configure_prefetch(3)
            results['paging'] = self.optimize_paging(disable_executive=True)
            results['cache'] = self.set_large_system_cache(enable=False)
            results['io_lock'] = self.optimize_io_page_lock_limit()
        
        success_count = sum(results.values())
        print(f"[MEMORY] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        print("[MEMORY] ⚠ Reinicie o PC para aplicar todas as mudanças")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status atual das configurações de memória"""
        status = {}
        
        try:
            # Verifica compressão
            result = subprocess.run(
                'powershell -Command "(Get-MMAgent).MemoryCompression"',
                shell=True, capture_output=True, text=True
            )
            status['compression'] = "Ativada" if "True" in result.stdout else "Desativada"
        except:
            status['compression'] = "Desconhecido"
        
        status['superfetch'] = self._get_registry_value(self.PREFETCH_KEY, "EnableSuperfetch")
        status['prefetch'] = self._get_registry_value(self.PREFETCH_KEY, "EnablePrefetcher")
        status['paging_executive'] = self._get_registry_value(self.MEMORY_KEY, "DisablePagingExecutive")
        
        return status


# Singleton
_instance = None

def get_optimizer() -> MemoryOptimizerPro:
    global _instance
    if _instance is None:
        _instance = MemoryOptimizerPro()
    return _instance


if __name__ == "__main__":
    optimizer = MemoryOptimizerPro()
    print("Status atual:", optimizer.get_status())
