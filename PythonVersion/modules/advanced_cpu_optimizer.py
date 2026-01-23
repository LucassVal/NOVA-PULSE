"""
NovaPulse - Advanced CPU Optimizer
C-States, Turbo Boost, Large Pages, e otimizações avançadas
"""
import winreg
import subprocess
import ctypes
from typing import Dict, Optional


class AdvancedCPUOptimizer:
    """
    Otimizações avançadas de CPU
    
    Features:
    - C-States control (desativa estados de economia)
    - Turbo Boost lock (força turbo sempre ativo)
    - Large System Cache
    - Processor scheduling otimizado
    """
    
    POWER_KEY = r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings"
    PROCESSOR_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, 
                           value_type=winreg.REG_DWORD, hive=winreg.HKEY_LOCAL_MACHINE) -> bool:
        try:
            key = winreg.CreateKeyEx(hive, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def _run_powercfg(self, args: str) -> bool:
        try:
            result = subprocess.run(
                f"powercfg {args}",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode == 0
        except:
            return False
    
    def disable_c_states(self) -> bool:
        """
        Desativa C-States profundos do processador
        C-States economizam energia mas aumentam latência ao acordar
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Desativando C-States profundos...")
        
        # Desativa via powercfg - Processor Idle Disable
        # GUID do Processor Power Management: 54533251-82be-4824-96c1-47b60b740d00
        # Sub-GUID Idle Disable: 5d76a2ca-e8c0-402f-a133-2158492d58ad
        
        success = self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 5d76a2ca-e8c0-402f-a133-2158492d58ad 1")
        self._run_powercfg("-setactive scheme_current")
        
        if success:
            print("[CPU ADV] ✓ C-States profundos desativados (menor latência)")
            self.applied_changes['c_states'] = False
        
        return success
    
    def force_turbo_boost(self) -> bool:
        """
        Força Turbo Boost sempre ativo
        Processador mantém frequência máxima enquanto térmico permitir
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Forçando Turbo Boost...")
        
        # Processor Performance Boost Mode
        # 0 = Disabled, 1 = Enabled, 2 = Aggressive, 3 = Efficient Aggressive
        success = self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2")
        self._run_powercfg("-setactive scheme_current")
        
        # Minimum processor state = 100% (força frequência alta)
        self._run_powercfg("-setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c 100")
        self._run_powercfg("-setactive scheme_current")
        
        if success:
            print("[CPU ADV] ✓ Turbo Boost forçado (modo agressivo)")
            self.applied_changes['turbo_boost'] = True
        
        return success
    
    def enable_large_system_cache(self) -> bool:
        """
        Habilita Large System Cache
        Usa mais RAM para cache de disco (melhor I/O)
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Habilitando Large System Cache...")
        
        success = self._set_registry_value(
            self.PROCESSOR_KEY,
            "LargeSystemCache",
            1
        )
        
        if success:
            print("[CPU ADV] ✓ Large System Cache habilitado")
            self.applied_changes['large_cache'] = True
        
        return success
    
    def optimize_processor_scheduling(self) -> bool:
        """
        Otimiza scheduling do processador para foreground apps
        0 = Shorter quantum for foreground, 38 = Longer quantum for background
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Otimizando processor scheduling...")
        
        # Win32PrioritySeparation
        # 38 = Short-quantum, foreground boost (melhor para gaming)
        # 2 = Long-quantum, no boost (melhor para servidores)
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\PriorityControl",
            "Win32PrioritySeparation",
            38
        )
        
        if success:
            print("[CPU ADV] ✓ Foreground apps priorizados")
            self.applied_changes['scheduling'] = True
        
        return success
    
    def disable_power_throttling(self) -> bool:
        """
        Desativa Power Throttling do Windows
        Windows 10+ throttles apps em background - desativar para performance
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Desativando Power Throttling...")
        
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling",
            "PowerThrottlingOff",
            1
        )
        
        if success:
            print("[CPU ADV] ✓ Power Throttling desativado")
            self.applied_changes['power_throttling'] = False
        
        return success
    
    def optimize_interrupt_affinity(self) -> bool:
        """
        Otimiza afinidade de interrupções
        Distribui melhor IRQs entre cores
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Otimizando interrupt affinity...")
        
        # Habilita interrupt affinity policy
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel",
            "DistributeTimers",
            1
        )
        
        if success:
            print("[CPU ADV] ✓ Timer distribution otimizado")
            self.applied_changes['interrupt_affinity'] = True
        
        return success
    
    def set_svchost_splitting(self) -> bool:
        """
        Configura splitting de svchost para sistemas com mais RAM
        Separa serviços em processos individuais (melhor para debugging e isolamento)
        """
        if not self.is_admin:
            return False
        
        print("[CPU ADV] Configurando svchost splitting...")
        
        # SvcHostSplitThresholdInKB - define threshold para split
        # 0 = Força split, alto valor = agrupa
        # Para 16GB+ RAM, podemos forçar split
        success = self._set_registry_value(
            r"SYSTEM\CurrentControlSet\Control",
            "SvcHostSplitThresholdInKB",
            0x00380000  # ~3.5GB threshold
        )
        
        if success:
            print("[CPU ADV] ✓ Svchost splitting configurado")
            self.applied_changes['svchost_split'] = True
        
        return success
    
    def apply_all_optimizations(self) -> Dict[str, bool]:
        """Aplica todas as otimizações avançadas de CPU"""
        print("\n[CPU ADV] Aplicando otimizações avançadas de CPU...")
        
        results = {}
        
        results['c_states'] = self.disable_c_states()
        results['turbo_boost'] = self.force_turbo_boost()
        results['large_cache'] = self.enable_large_system_cache()
        results['scheduling'] = self.optimize_processor_scheduling()
        results['power_throttling'] = self.disable_power_throttling()
        results['interrupt'] = self.optimize_interrupt_affinity()
        results['svchost'] = self.set_svchost_splitting()
        
        success_count = sum(results.values())
        print(f"[CPU ADV] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status das otimizações"""
        return {
            'applied': self.applied_changes
        }


# Singleton
_instance = None

def get_optimizer() -> AdvancedCPUOptimizer:
    global _instance
    if _instance is None:
        _instance = AdvancedCPUOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = AdvancedCPUOptimizer()
    optimizer.apply_all_optimizations()
