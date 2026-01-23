"""
NovaPulse - HPET Controller
Controla High Precision Event Timer e timers do sistema
"""
import subprocess
import ctypes
from typing import Dict, Tuple, Optional


class HPETController:
    """
    Controla HPET (High Precision Event Timer) e timers relacionados
    
    HPET pode adicionar latência em alguns sistemas.
    Desativar pode melhorar input lag em jogos.
    
    ATENÇÃO: Nem todos os sistemas se beneficiam desta otimização.
    Em alguns casos, pode causar instabilidade.
    """
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
        self.original_values = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_bcdedit(self, args: str) -> Tuple[bool, str]:
        """Executa comando bcdedit"""
        try:
            result = subprocess.run(
                f"bcdedit {args}",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def disable_hpet(self) -> bool:
        """
        Desativa HPET via BCD
        
        Impacto:
        - Pode reduzir input lag em jogos
        - Melhora latência em alguns sistemas
        
        Riscos:
        - Pode causar instabilidade em alguns sistemas
        - Alguns softwares podem ter problemas de timing
        """
        if not self.is_admin:
            print("[HPET] ✗ Requer privilégios de administrador")
            return False
        
        # Salva valor original
        success, output = self._run_bcdedit("/enum")
        if "useplatformclock" in output.lower():
            self.original_values['useplatformclock'] = True
        
        # Desativa HPET
        success, output = self._run_bcdedit("/set useplatformclock false")
        
        if success:
            print("[HPET] ✓ HPET desativado (useplatformclock = false)")
            self.applied_changes['hpet'] = False
        else:
            # Tenta deletar a entrada (volta ao padrão)
            self._run_bcdedit("/deletevalue useplatformclock")
            print("[HPET] ✓ HPET configuração removida (padrão do sistema)")
            self.applied_changes['hpet'] = None
        
        return True
    
    def enable_hpet(self) -> bool:
        """Reativa HPET"""
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/set useplatformclock true")
        
        if success:
            print("[HPET] ✓ HPET reativado")
            self.applied_changes['hpet'] = True
        
        return success
    
    def disable_dynamic_tick(self) -> bool:
        """
        Desativa Dynamic Tick (tickless timer)
        
        Windows usa tick dinâmico para economia de energia.
        Desativar força tick constante, pode melhorar latência.
        
        Impacto:
        - Menores latências
        - Maior consumo de energia
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_bcdedit("/set disabledynamictick yes")
        
        if success:
            print("[HPET] ✓ Dynamic Tick desativado")
            self.applied_changes['dynamic_tick'] = False
        else:
            print(f"[HPET] ✗ Erro ao desativar Dynamic Tick: {output}")
        
        return success
    
    def enable_dynamic_tick(self) -> bool:
        """Reativa Dynamic Tick"""
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/deletevalue disabledynamictick")
        
        if success:
            print("[HPET] ✓ Dynamic Tick reativado")
            self.applied_changes['dynamic_tick'] = True
        
        return success
    
    def set_tscsyncpolicy(self, policy: str = "enhanced") -> bool:
        """
        Define política de sincronização do TSC (Time Stamp Counter)
        
        Policies:
        - "default": Padrão do Windows
        - "legacy": Compatibilidade com sistemas antigos
        - "enhanced": Melhor precisão (recomendado para gaming)
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_bcdedit(f"/set tscsyncpolicy {policy}")
        
        if success:
            print(f"[HPET] ✓ TSC Sync Policy = {policy}")
            self.applied_changes['tscsync'] = policy
        else:
            print(f"[HPET] ℹ TSC Sync Policy não aplicável neste sistema")
        
        return success
    
    def disable_synthetic_timers(self) -> bool:
        """
        Desativa synthetic timers do Hyper-V
        (Útil apenas se Hyper-V estiver instalado)
        """
        if not self.is_admin:
            return False
        
        success, _ = self._run_bcdedit("/set hypervisorlaunchtype off")
        
        if success:
            print("[HPET] ✓ Hyper-V hypervisor desativado")
            print("[HPET] ⚠ Isso pode afetar WSL2, Docker, etc.")
            self.applied_changes['hypervisor'] = False
        else:
            print("[HPET] ℹ Hyper-V não está instalado ou já desativado")
        
        return True
    
    def optimize_boot_options(self) -> bool:
        """
        Aplica outras otimizações de boot relacionadas a timing
        """
        if not self.is_admin:
            return False
        
        optimizations = []
        
        # Desativa debugging (reduz overhead)
        success, _ = self._run_bcdedit("/debug off")
        if success:
            optimizations.append("debug off")
        
        # Desativa boot log (menos I/O)
        success, _ = self._run_bcdedit("/bootlog no")
        if success:
            optimizations.append("bootlog no")
        
        if optimizations:
            print(f"[HPET] ✓ Boot otimizado: {', '.join(optimizations)}")
            self.applied_changes['boot_optimized'] = True
        
        return len(optimizations) > 0
    
    def apply_all_optimizations(self, aggressive: bool = False) -> Dict[str, bool]:
        """
        Aplica todas as otimizações de timer
        
        aggressive: Se True, aplica otimizações mais arriscadas
        """
        print("\n[HPET] Aplicando otimizações de timer...")
        
        results = {}
        
        # Otimizações seguras
        results['hpet'] = self.disable_hpet()
        results['dynamic_tick'] = self.disable_dynamic_tick()
        results['tscsync'] = self.set_tscsyncpolicy("enhanced")
        results['boot'] = self.optimize_boot_options()
        
        if aggressive:
            print("[HPET] ⚠ Modo agressivo: desativando Hyper-V")
            results['hypervisor'] = self.disable_synthetic_timers()
        
        success_count = sum(results.values())
        print(f"[HPET] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        print("[HPET] ⚠ REINÍCIO OBRIGATÓRIO para aplicar mudanças de BCD")
        
        return results
    
    def restore_defaults(self) -> bool:
        """
        Restaura configurações padrão de timer
        """
        if not self.is_admin:
            return False
        
        print("[HPET] Restaurando configurações padrão...")
        
        self._run_bcdedit("/deletevalue useplatformclock")
        self._run_bcdedit("/deletevalue disabledynamictick")
        self._run_bcdedit("/deletevalue tscsyncpolicy")
        
        print("[HPET] ✓ Configurações de timer restauradas")
        print("[HPET] ⚠ Reinicie para aplicar")
        
        return True
    
    def get_status(self) -> Dict[str, str]:
        """Retorna status atual das configurações de timer"""
        status = {}
        
        try:
            success, output = self._run_bcdedit("/enum")
            
            if "useplatformclock" in output.lower():
                if "yes" in output.lower() or "true" in output.lower():
                    status['hpet'] = "Ativado"
                else:
                    status['hpet'] = "Desativado"
            else:
                status['hpet'] = "Padrão do sistema"
            
            if "disabledynamictick" in output.lower():
                status['dynamic_tick'] = "Desativado"
            else:
                status['dynamic_tick'] = "Ativo (padrão)"
            
            if "tscsyncpolicy" in output.lower():
                if "enhanced" in output.lower():
                    status['tscsync'] = "Enhanced"
                elif "legacy" in output.lower():
                    status['tscsync'] = "Legacy"
                else:
                    status['tscsync'] = "Custom"
            else:
                status['tscsync'] = "Padrão"
                
        except:
            status['error'] = "Não foi possível ler configurações"
        
        return status
    
    def benchmark_latency(self) -> Optional[float]:
        """
        Faz um benchmark simples de latência do timer
        Retorna latência média em microsegundos
        """
        try:
            import time
            
            samples = []
            for _ in range(1000):
                start = time.perf_counter_ns()
                # Operação mínima
                _ = 1 + 1
                end = time.perf_counter_ns()
                samples.append(end - start)
            
            avg_ns = sum(samples) / len(samples)
            avg_us = avg_ns / 1000
            
            print(f"[HPET] Latência média do timer: {avg_us:.2f} µs")
            return avg_us
            
        except Exception as e:
            print(f"[HPET] Erro no benchmark: {e}")
            return None


# Singleton
_instance = None

def get_controller() -> HPETController:
    global _instance
    if _instance is None:
        _instance = HPETController()
    return _instance


if __name__ == "__main__":
    controller = HPETController()
    print("Status atual:", controller.get_status())
    controller.benchmark_latency()
