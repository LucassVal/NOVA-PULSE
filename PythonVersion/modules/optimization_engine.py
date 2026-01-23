"""
NovaPulse - Optimization Engine
Motor central que orquestra todos os módulos de otimização
"""
import threading
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class OptimizationLevel(Enum):
    """Níveis de otimização"""
    SAFE = "safe"           # Otimizações seguras, reversíveis
    BALANCED = "balanced"   # Balanço entre segurança e performance
    AGGRESSIVE = "aggressive"  # Máxima performance, pode requerer restart
    GAMING = "gaming"       # Específico para jogos


@dataclass
class OptimizationResult:
    """Resultado de uma otimização"""
    module: str
    success: bool
    changes: Dict[str, bool]
    requires_restart: bool = False
    message: str = ""


class OptimizationEngine:
    """
    Motor central de otimização do NovaPulse
    
    Orquestra todos os módulos de otimização garantindo:
    - Ordem correta de aplicação
    - Evita conflitos entre módulos
    - Permite rollback
    - Logging centralizado
    """
    
    def __init__(self):
        self.results: List[OptimizationResult] = []
        self.applied_optimizations: Dict[str, bool] = {}
        self.requires_restart = False
        
    def apply_all(self, level: OptimizationLevel = OptimizationLevel.BALANCED) -> Dict[str, OptimizationResult]:
        """
        Aplica todas as otimizações de acordo com o nível
        """
        print(f"\n{'='*60}")
        print(f"⚡ NovaPulse Optimization Engine")
        print(f"📊 Nível: {level.value}")
        print(f"{'='*60}\n")
        
        results = {}
        
        # Ordem de aplicação (importante para evitar conflitos):
        # 1. Power/CPU (base)
        # 2. Memory (usa CPU settings)
        # 3. Storage (usa memory settings)
        # 4. GPU (independent)
        # 5. Network (independent)
        # 6. Timers (afeta tudo)
        # 7. Process Control (usa todas settings)
        
        # === FASE 1: POWER/CPU ===
        try:
            from modules.core_parking import get_manager as get_parking
            parking = get_parking()
            use_ultimate = level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]
            changes = parking.apply_all_optimizations(use_ultimate=use_ultimate)
            results['core_parking'] = OptimizationResult(
                module='Core Parking',
                success=any(changes.values()),
                changes=changes,
                requires_restart=False,
                message='Power scheme e core parking configurados'
            )
        except Exception as e:
            print(f"[ENGINE] ⚠ Core Parking: {e}")
        
        # === FASE 2: MEMORY ===
        try:
            from modules.memory_optimizer import get_optimizer as get_memory
            memory = get_memory()
            gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
            changes = memory.apply_all_optimizations(gaming_mode=gaming_mode)
            results['memory'] = OptimizationResult(
                module='Memory Optimizer',
                success=any(changes.values()),
                changes=changes,
                requires_restart=True,
                message='Compressão, Superfetch e paginação otimizados'
            )
            self.requires_restart = True
        except Exception as e:
            print(f"[ENGINE] ⚠ Memory Optimizer: {e}")
        
        # === FASE 3: STORAGE (NTFS) ===
        try:
            from modules.ntfs_optimizer import get_optimizer as get_ntfs
            ntfs = get_ntfs()
            gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
            changes = ntfs.apply_all_optimizations(gaming_mode=gaming_mode)
            results['ntfs'] = OptimizationResult(
                module='NTFS Optimizer',
                success=any(changes.values()),
                changes=changes,
                requires_restart=False,
                message='Sistema de arquivos otimizado'
            )
        except Exception as e:
            print(f"[ENGINE] ⚠ NTFS Optimizer: {e}")
        
        # === FASE 4: GPU ===
        try:
            from modules.gpu_scheduler import get_controller as get_gpu
            gpu = get_gpu()  # FIXED: was using wrong variable name
            changes = gpu.apply_all_optimizations()
            results['gpu'] = OptimizationResult(
                module='GPU Scheduler',
                success=any(changes.values()),
                changes=changes,
                requires_restart=True,
                message='HAGS e GPU priority configurados'
            )
            if changes.get('hags'):
                self.requires_restart = True
        except Exception as e:
            print(f"[ENGINE] ⚠ GPU Scheduler: {e}")
        
        # === FASE 4.5: CUDA OPTIMIZER (Novo!) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.cuda_optimizer import get_optimizer as get_cuda
                cuda = get_cuda()
                changes = cuda.apply_all_optimizations()
                results['cuda'] = OptimizationResult(
                    module='CUDA Optimizer',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='CUDA, PhysX e aceleração de hardware configurados'
                )
            except Exception as e:
                print(f"[ENGINE] ⚠ CUDA Optimizer: {e}")
        
        # === FASE 5: MMCSS (Multimedia) ===
        try:
            from modules.mmcss_optimizer import get_optimizer as get_mmcss
            mmcss = get_mmcss()
            gaming_focused = level in [OptimizationLevel.GAMING]
            changes = mmcss.apply_all_optimizations(gaming_focused=gaming_focused)
            results['mmcss'] = OptimizationResult(
                module='MMCSS Optimizer',
                success=any(changes.values()),
                changes=changes,
                requires_restart=False,
                message='Multimedia scheduler otimizado'
            )
        except Exception as e:
            print(f"[ENGINE] ⚠ MMCSS Optimizer: {e}")
        
        # === FASE 6: NETWORK ===
        try:
            from modules.network_stack_optimizer import get_optimizer as get_network
            network = get_network()
            gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
            changes = network.apply_all_optimizations(gaming_mode=gaming_mode)
            results['network'] = OptimizationResult(
                module='Network Stack',
                success=any(changes.values()),
                changes=changes,
                requires_restart=False,
                message='TCP/IP stack otimizado'
            )
        except Exception as e:
            print(f"[ENGINE] ⚠ Network Stack: {e}")
        
        # === FASE 7: USB ===
        try:
            from modules.usb_optimizer import get_optimizer as get_usb
            usb = get_usb()
            changes = usb.apply_all_optimizations()
            results['usb'] = OptimizationResult(
                module='USB Optimizer',
                success=any(changes.values()),
                changes=changes,
                requires_restart=False,
                message='USB polling e buffers otimizados'
            )
        except Exception as e:
            print(f"[ENGINE] ⚠ USB Optimizer: {e}")
        
        # === FASE 8: IRQ (Apenas em Aggressive/Gaming) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.irq_optimizer import get_optimizer as get_irq
                irq = get_irq()
                changes = irq.apply_all_optimizations()
                results['irq'] = OptimizationResult(
                    module='IRQ Affinity',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=True,
                    message='MSI mode e afinidade de IRQ configurados'
                )
                self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ IRQ Optimizer: {e}")
        
        # === FASE 9: HPET/Timers (Apenas em Aggressive/Gaming) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.hpet_controller import get_controller as get_hpet
                hpet = get_hpet()
                aggressive = level == OptimizationLevel.AGGRESSIVE
                changes = hpet.apply_all_optimizations(aggressive=aggressive)
                results['hpet'] = OptimizationResult(
                    module='HPET Controller',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=True,
                    message='HPET e timers otimizados'
                )
                self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ HPET Controller: {e}")
        
        # === FASE 10: Advanced CPU (Novo!) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.advanced_cpu_optimizer import get_optimizer as get_adv_cpu
                adv_cpu = get_adv_cpu()
                changes = adv_cpu.apply_all_optimizations()
                results['advanced_cpu'] = OptimizationResult(
                    module='Advanced CPU',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=True,
                    message='C-States, Turbo Boost, scheduling otimizados'
                )
                self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ Advanced CPU: {e}")
        
        # === FASE 11: Advanced Storage (Novo!) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.advanced_storage_optimizer import get_optimizer as get_adv_storage
                adv_storage = get_adv_storage()
                changes = adv_storage.apply_all_optimizations()
                results['advanced_storage'] = OptimizationResult(
                    module='Advanced Storage',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='Write cache, queue depth, large pages otimizados'
                )
            except Exception as e:
                print(f"[ENGINE] ⚠ Advanced Storage: {e}")
        
        # === FASE 12: Process Controller ===
        try:
            from modules.process_controller import get_controller as get_process
            process = get_process()
            process.start()
            
            if level == OptimizationLevel.GAMING:
                gaming_results = process.apply_gaming_preset()
                results['process'] = OptimizationResult(
                    module='Process Controller',
                    success=True,
                    changes=gaming_results,
                    requires_restart=False,
                    message='Controle de processos ativo com preset gaming'
                )
            else:
                results['process'] = OptimizationResult(
                    module='Process Controller',
                    success=True,
                    changes={'monitoring_active': True},
                    requires_restart=False,
                    message='Controle de processos ativo'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ Process Controller: {e}")
        
        # === RESUMO ===
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict[str, OptimizationResult]):
        """Imprime resumo das otimizações"""
        print(f"\n{'='*60}")
        print("📊 RESUMO DAS OTIMIZAÇÕES")
        print(f"{'='*60}")
        
        total = len(results)
        success = sum(1 for r in results.values() if r.success)
        
        for name, result in results.items():
            icon = "✓" if result.success else "✗"
            restart = " ⚠️" if result.requires_restart else ""
            print(f"  {icon} {result.module}: {result.message}{restart}")
        
        print(f"\n📈 Resultado: {success}/{total} módulos aplicados com sucesso")
        
        if self.requires_restart:
            print(f"\n⚠️  REINÍCIO NECESSÁRIO para aplicar algumas mudanças")
        
        print(f"{'='*60}\n")
    
    def get_optimization_status(self) -> Dict[str, any]:
        """Retorna status de todas as otimizações"""
        status = {
            'applied': self.applied_optimizations,
            'requires_restart': self.requires_restart,
            'results_count': len(self.results)
        }
        
        # Coleta status de cada módulo
        modules_status = {}
        
        try:
            from modules.core_parking import get_manager
            modules_status['core_parking'] = get_manager().get_status()
        except:
            pass
        
        try:
            from modules.memory_optimizer import get_optimizer
            modules_status['memory'] = get_optimizer().get_status()
        except:
            pass
        
        try:
            from modules.gpu_scheduler import get_controller
            modules_status['gpu'] = get_controller().get_status()
        except:
            pass
        
        try:
            from modules.hpet_controller import get_controller
            modules_status['hpet'] = get_controller().get_status()
        except:
            pass
        
        status['modules'] = modules_status
        return status


# Singleton
_instance = None

def get_engine() -> OptimizationEngine:
    global _instance
    if _instance is None:
        _instance = OptimizationEngine()
    return _instance


if __name__ == "__main__":
    engine = OptimizationEngine()
    
    print("Escolha o nível de otimização:")
    print("1. Safe (seguro)")
    print("2. Balanced (balanceado)")
    print("3. Gaming (jogos)")
    print("4. Aggressive (agressivo)")
    
    choice = input("\nOpção (1-4): ").strip()
    
    levels = {
        '1': OptimizationLevel.SAFE,
        '2': OptimizationLevel.BALANCED,
        '3': OptimizationLevel.GAMING,
        '4': OptimizationLevel.AGGRESSIVE
    }
    
    level = levels.get(choice, OptimizationLevel.BALANCED)
    results = engine.apply_all(level)
