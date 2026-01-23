"""
NovaPulse - Core Parking Manager
Controla o estacionamento de núcleos da CPU (Core Parking)
"""
import winreg
import ctypes
import subprocess
from typing import Dict, Optional


class CoreParkingManager:
    """
    Gerencia Core Parking do Windows
    
    Core Parking é um recurso que "dorme" núcleos inativos para economizar energia.
    Desativar melhora responsividade em troca de maior consumo de energia.
    """
    
    # GUIDs dos power settings
    PROCESSOR_SUBGROUP = "54533251-82be-4824-96c1-47b60b740d00"
    
    # Core Parking settings
    CORE_PARKING_MIN = "0cc5b647-c1df-4637-891a-dec35c318583"  # Min cores
    CORE_PARKING_MAX = "ea062031-0e34-4ff1-9b6d-eb1059334028"  # Max cores
    CORE_PARKING_INCREASE_TIME = "2ddd5a84-5a71-437e-912a-db0b8c788732"
    CORE_PARKING_DECREASE_TIME = "dfd10d17-d5eb-45dd-877a-9a34ddd15c82"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_powercfg(self, args: str) -> bool:
        """Executa comando powercfg"""
        try:
            result = subprocess.run(
                f"powercfg {args}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _set_power_setting(self, setting_guid: str, value: int, ac: bool = True) -> bool:
        """Define uma configuração de energia via powercfg"""
        power_type = "/setacvalueindex" if ac else "/setdcvalueindex"
        
        cmd = f"{power_type} scheme_current sub_processor {setting_guid} {value}"
        return self._run_powercfg(cmd)
    
    def disable_core_parking(self) -> bool:
        """
        Desativa Core Parking completamente
        Todos os núcleos ficam sempre ativos
        
        Impacto:
        - ⚡ Resposta mais rápida
        - ⚡ Menos stuttering em jogos
        - 🔋 Maior consumo de energia
        """
        if not self.is_admin:
            print("[PARKING] ✗ Requer privilégios de administrador")
            return False
        
        print("[PARKING] Desativando Core Parking...")
        
        success = True
        
        # Min cores unparked = 100% (todos ativos)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, 100, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, 100, ac=False)
        
        # Max cores unparked = 100%
        success &= self._set_power_setting(self.CORE_PARKING_MAX, 100, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MAX, 100, ac=False)
        
        # Aplica as mudanças
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print("[PARKING] ✓ Core Parking desativado (100% cores ativos)")
            self.applied_changes['parking_disabled'] = True
        else:
            print("[PARKING] ✗ Erro ao desativar Core Parking")
        
        return success
    
    def enable_core_parking(self, min_percent: int = 50) -> bool:
        """
        Reativa Core Parking com configuração personalizada
        min_percent: Mínimo de cores que ficam ativos (0-100)
        """
        if not self.is_admin:
            return False
        
        min_percent = max(0, min(100, min_percent))
        
        success = True
        success &= self._set_power_setting(self.CORE_PARKING_MIN, min_percent, ac=True)
        success &= self._set_power_setting(self.CORE_PARKING_MIN, min_percent, ac=False)
        
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print(f"[PARKING] ✓ Core Parking reativado (min {min_percent}% cores)")
            self.applied_changes['parking_disabled'] = False
        
        return success
    
    def optimize_parking_timers(self) -> bool:
        """
        Otimiza timers de parking para resposta mais rápida
        - Tempo para aumentar cores: Reduzido
        - Tempo para diminuir cores: Aumentado
        """
        if not self.is_admin:
            return False
        
        success = True
        
        # Increase time: 1ms (reage rápido a carga)
        success &= self._set_power_setting(self.CORE_PARKING_INCREASE_TIME, 1, ac=True)
        
        # Decrease time: 100ms (demora mais para dormir)
        success &= self._set_power_setting(self.CORE_PARKING_DECREASE_TIME, 100, ac=True)
        
        self._run_powercfg("/setactive scheme_current")
        
        if success:
            print("[PARKING] ✓ Timers de parking otimizados")
            self.applied_changes['timers_optimized'] = True
        
        return success
    
    def set_high_performance_scheme(self) -> bool:
        """
        Ativa plano de energia High Performance
        (Desativa muitas otimizações de economia automaticamente)
        """
        if not self.is_admin:
            return False
        
        # GUID do High Performance scheme
        # 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
        success = self._run_powercfg("/setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
        
        if success:
            print("[PARKING] ✓ Plano High Performance ativado")
            self.applied_changes['high_performance'] = True
        else:
            # Tenta criar se não existir
            self._run_powercfg("/duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
            success = self._run_powercfg("/setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
            if success:
                print("[PARKING] ✓ Plano High Performance criado e ativado")
                self.applied_changes['high_performance'] = True
        
        return success
    
    def create_ultimate_performance_scheme(self) -> bool:
        """
        Cria e ativa plano Ultimate Performance (Windows 10 Pro+)
        """
        if not self.is_admin:
            return False
        
        # Tenta ativar Ultimate Performance
        # e9a42b02-d5df-448d-aa00-03f14749eb61
        success = self._run_powercfg("/setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
        
        if not success:
            # Tenta criar o scheme
            result = subprocess.run(
                "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
                shell=True, capture_output=True, text=True
            )
            if "e9a42b02" in result.stdout or result.returncode == 0:
                success = self._run_powercfg("/setactive e9a42b02-d5df-448d-aa00-03f14749eb61")
        
        if success:
            print("[PARKING] ✓ Ultimate Performance ativado")
            self.applied_changes['ultimate_performance'] = True
        else:
            print("[PARKING] ℹ Ultimate Performance não disponível, usando High Performance")
            return self.set_high_performance_scheme()
        
        return success
    
    def apply_all_optimizations(self, use_ultimate: bool = True) -> Dict[str, bool]:
        """
        Aplica todas as otimizações de Core Parking
        """
        print("\n[PARKING] Aplicando otimizações de Core Parking...")
        
        results = {}
        
        # Primeiro define o power scheme
        if use_ultimate:
            results['power_scheme'] = self.create_ultimate_performance_scheme()
        else:
            results['power_scheme'] = self.set_high_performance_scheme()
        
        # Desativa parking
        results['disable_parking'] = self.disable_core_parking()
        
        # Otimiza timers
        results['timers'] = self.optimize_parking_timers()
        
        success_count = sum(results.values())
        print(f"[PARKING] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, str]:
        """Retorna status atual do Core Parking"""
        status = {}
        
        try:
            # Verifica plano ativo
            result = subprocess.run(
                "powercfg /getactivescheme",
                shell=True, capture_output=True, text=True
            )
            if "Ultimate" in result.stdout:
                status['power_scheme'] = "Ultimate Performance"
            elif "High" in result.stdout:
                status['power_scheme'] = "High Performance"
            elif "Balanced" in result.stdout:
                status['power_scheme'] = "Balanced"
            else:
                status['power_scheme'] = result.stdout.strip()
        except:
            status['power_scheme'] = "Desconhecido"
        
        return status


# Singleton
_instance = None

def get_manager() -> CoreParkingManager:
    global _instance
    if _instance is None:
        _instance = CoreParkingManager()
    return _instance


if __name__ == "__main__":
    manager = CoreParkingManager()
    print("Status atual:", manager.get_status())
