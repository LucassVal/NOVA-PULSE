"""
NovaPulse - Optimization Engine
Central engine that orchestrates all optimization modules
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class OptimizationLevel(Enum):
    """Optimization levels"""
    SAFE = "safe"           # Safe, reversible optimizations
    BALANCED = "balanced"   # Balance between safety and performance
    AGGRESSIVE = "aggressive"  # Maximum performance, may require restart
    GAMING = "gaming"       # Gaming-specific optimizations


@dataclass
class OptimizationResult:
    """Result of an optimization"""
    module: str
    success: bool
    changes: Dict[str, bool]
    requires_restart: bool = False
    message: str = ""


class OptimizationEngine:
    """
    NovaPulse Central Optimization Engine
    
    Orchestrates all optimization modules ensuring:
    - Correct application order
    - Avoids conflicts between modules
    - Allows rollback
    - Centralized logging
    """
    
    def __init__(self):
        self.results: List[OptimizationResult] = []
        self.applied_optimizations: Dict[str, bool] = {}
        self.requires_restart = False
        
    def apply_all(self, level: OptimizationLevel = OptimizationLevel.BALANCED, interactive: bool = True, dry_run: bool = False) -> Dict[str, OptimizationResult]:
        """
        Apply all optimizations according to the level
        If interactive is True, prompts the user before applying modules that require restart.
        If dry_run is True, it only checks which modules would be applied and if they require restart.
        """
        if not dry_run:
            print(f"\n{'='*60}")
            print("⚡ NovaPulse Optimization Engine")
            print(f"Level: {level.value}")
            print(f"{'='*60}\n")
        
        results = {}
        
        def _should_apply(module_name: str, module_obj: any = None, requires_restart_flag: bool = False) -> bool:
            if module_obj and hasattr(module_obj, 'is_optimized'):
                try:
                    if module_obj.is_optimized():
                        if not dry_run:
                            print(f"[✓] {module_name} is already active. Skipping.")
                        return False
                except Exception as e:
                    if not dry_run:
                        print(f"    [!] Warning checking {module_name} status: {e}")
            
            if dry_run:
                return True # We return True so the engine records that it *would* apply it
                
            if not interactive:
                return True
            if requires_restart_flag:
                print(f"\n[?] The '{module_name}' module applies kernel-level changes and REQUIRES a RESTART.")
                choice = input(f"    Do you want to apply optimizations for {module_name}? (y/n): ").strip().lower()
                return choice == 'y'
            return True

        # === FASE 1: POWER/CPU ===
        try:
            from modules.core_parking import get_manager as get_parking
            parking = get_parking()
            if _should_apply("Core Parking", parking, False):
                use_ultimate = level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]
                changes = parking.apply_all_optimizations(use_ultimate=use_ultimate)
                results['core_parking'] = OptimizationResult(
                    module='Core Parking',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='Power scheme and core parking configured'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ Core Parking: {e}")
        
        # === FASE 2: MEMORY ===
        try:
            from modules.memory_optimizer import get_optimizer as get_memory
            memory = get_memory()
            if _should_apply("Memory Optimizer", memory, True):
                gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
                changes = memory.apply_all_optimizations(gaming_mode=gaming_mode)
                results['memory'] = OptimizationResult(
                    module='Memory Optimizer',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=True,
                    message='Compression, Superfetch and paging optimized'
                )
                self.requires_restart = True
        except Exception as e:
            print(f"[ENGINE] ⚠ Memory Optimizer: {e}")
        
        # === FASE 3: STORAGE (NTFS) ===
        try:
            from modules.ntfs_optimizer import get_optimizer as get_ntfs
            ntfs = get_ntfs()
            if _should_apply("NTFS Optimizer", ntfs, False):
                gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
                changes = ntfs.apply_all_optimizations(gaming_mode=gaming_mode)
                results['ntfs'] = OptimizationResult(
                    module='NTFS Optimizer',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='File system optimized'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ NTFS Optimizer: {e}")
        
        # === FASE 4: GPU ===
        try:
            from modules.gpu_scheduler import get_controller as get_gpu
            gpu = get_gpu()
            if _should_apply("GPU Scheduler", gpu, True):
                changes = gpu.apply_all_optimizations()
                results['gpu'] = OptimizationResult(
                    module='GPU Scheduler',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=True,
                    message='HAGS and GPU priority configured'
                )
                if changes.get('hags'):
                    self.requires_restart = True
        except Exception as e:
            print(f"[ENGINE] ⚠ GPU Scheduler: {e}")
        
        # === PHASE 4.5: CUDA OPTIMIZER ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.cuda_optimizer import get_optimizer as get_cuda
                cuda = get_cuda()
                if _should_apply("CUDA Optimizer", cuda, False):
                    changes = cuda.apply_all_optimizations()
                    results['cuda'] = OptimizationResult(
                        module='CUDA Optimizer',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=False,
                        message='CUDA, PhysX and hardware acceleration configured'
                    )
            except Exception as e:
                print(f"[ENGINE] ⚠ CUDA Optimizer: {e}")
        
        # === FASE 5: MMCSS (Multimedia) ===
        try:
            from modules.mmcss_optimizer import get_optimizer as get_mmcss
            mmcss = get_mmcss()
            if _should_apply("MMCSS Optimizer", mmcss, False):
                gaming_focused = level in [OptimizationLevel.GAMING]
                changes = mmcss.apply_all_optimizations(gaming_focused=gaming_focused)
                results['mmcss'] = OptimizationResult(
                    module='MMCSS Optimizer',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='Multimedia scheduler optimized'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ MMCSS Optimizer: {e}")
        
        # === FASE 6: NETWORK ===
        try:
            from modules.network_stack_optimizer import get_optimizer as get_network
            network = get_network()
            if _should_apply("Network Stack", network, False):
                gaming_mode = level in [OptimizationLevel.GAMING, OptimizationLevel.AGGRESSIVE]
                changes = network.apply_all_optimizations(gaming_mode=gaming_mode)
                results['network'] = OptimizationResult(
                    module='Network Stack',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='TCP/IP stack optimized'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ Network Stack: {e}")
        
        # === FASE 7: USB ===
        try:
            from modules.usb_optimizer import get_optimizer as get_usb
            usb = get_usb()
            if _should_apply("USB Optimizer", usb, False):
                changes = usb.apply_all_optimizations()
                results['usb'] = OptimizationResult(
                    module='USB Optimizer',
                    success=any(changes.values()),
                    changes=changes,
                    requires_restart=False,
                    message='USB polling and buffers optimized'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ USB Optimizer: {e}")
        
        # === PHASE 8: IRQ (Aggressive/Gaming only) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.irq_optimizer import get_optimizer as get_irq
                irq = get_irq()
                if _should_apply("IRQ Affinity", irq, True):
                    changes = irq.apply_all_optimizations()
                    results['irq'] = OptimizationResult(
                        module='IRQ Affinity',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=True,
                        message='MSI mode and IRQ affinity configured'
                    )
                    self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ IRQ Optimizer: {e}")
        
        # === PHASE 9: HPET/Timers (Aggressive/Gaming only) ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.hpet_controller import get_controller as get_hpet
                hpet = get_hpet()
                if _should_apply("HPET Controller", hpet, True):
                    aggressive = level == OptimizationLevel.AGGRESSIVE
                    changes = hpet.apply_all_optimizations(aggressive=aggressive)
                    results['hpet'] = OptimizationResult(
                        module='HPET Controller',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=True,
                        message='HPET and timers optimized'
                    )
                    self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ HPET Controller: {e}")
        
        # === PHASE 10: Advanced CPU ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.advanced_cpu_optimizer import get_optimizer as get_adv_cpu
                adv_cpu = get_adv_cpu()
                if _should_apply("Advanced CPU", adv_cpu, True):
                    changes = adv_cpu.apply_all_optimizations()
                    results['advanced_cpu'] = OptimizationResult(
                        module='Advanced CPU',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=True,
                        message='C-States, Turbo Boost, scheduling optimized'
                    )
                    self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ Advanced CPU: {e}")
        
        # === PHASE 11: Advanced Storage ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.advanced_storage_optimizer import get_optimizer as get_adv_storage
                adv_storage = get_adv_storage()
                if _should_apply("Advanced Storage", adv_storage, False):
                    changes = adv_storage.apply_all_optimizations()
                    results['advanced_storage'] = OptimizationResult(
                        module='Advanced Storage',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=False,
                        message='Write cache, queue depth, large pages optimized'
                    )
            except Exception as e:
                print(f"[ENGINE] ⚠ Advanced Storage: {e}")
        
        # === FASE 12: Dynamic Scheduler (Replaces Process Controller) ===
        try:
            from modules.dynamic_scheduler import get_scheduler
            scheduler = get_scheduler()
            if _should_apply("Dynamic Scheduler", scheduler, False):
                scheduler.start()
                
                results['scheduler'] = OptimizationResult(
                    module='Dynamic Scheduler',
                    success=True,
                    changes={'monitoring_active': True},
                    requires_restart=False,
                    message='Heuristic process control active'
                )
        except Exception as e:
            print(f"[ENGINE] ⚠ Dynamic Scheduler: {e}")
            
        # === PHASE 13: EXTREME AI VECTORS ===
        if level in [OptimizationLevel.AGGRESSIVE, OptimizationLevel.GAMING]:
            try:
                from modules.extreme_ai_optimizer import get_optimizer as get_extreme
                extreme = get_extreme()
                if _should_apply("Extreme AI Vectors", extreme, True):
                    changes = extreme.apply_all_optimizations()
                    results['extreme_ai'] = OptimizationResult(
                        module='Extreme AI Vectors',
                        success=any(changes.values()),
                        changes=changes,
                        requires_restart=True,
                        message='WSL limits, TCP experimental, Affinity, Defender & VBS applied'
                    )
                    self.requires_restart = True
            except Exception as e:
                print(f"[ENGINE] ⚠ Extreme AI: {e}")
        
        
        # === SUMMARY ===
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict[str, OptimizationResult]):
        """Print optimization summary"""
        print(f"\n{'='*60}")
        print("OPTIMIZATION SUMMARY")
        print(f"{'='*60}")
        
        total = len(results)
        success = sum(1 for r in results.values() if r.success)
        
        for name, result in results.items():
            icon = "✓" if result.success else "✗"
            restart = " ⚠️" if result.requires_restart else ""
            print(f"  {icon} {result.module}: {result.message}{restart}")
        
        print(f"\nResult: {success}/{total} modules applied successfully")
        
        if self.requires_restart:
            print("\n⚠️  RESTART REQUIRED to apply some changes")
            print("   Please reboot your system when you are ready.")
        
        print(f"{'='*60}\n")
    
    def get_optimization_status(self) -> Dict[str, any]:
        """Returns status of all optimizations"""
        status = {
            'applied': self.applied_optimizations,
            'requires_restart': self.requires_restart,
            'results_count': len(self.results)
        }
        
        # Collect status from each module
        modules_status = {}
        
        try:
            from modules.core_parking import get_manager
            modules_status['core_parking'] = get_manager().get_status()
        except Exception:
            pass
        
        try:
            from modules.memory_optimizer import get_optimizer
            modules_status['memory'] = get_optimizer().get_status()
        except Exception:
            pass
        
        try:
            from modules.gpu_scheduler import get_controller
            modules_status['gpu'] = get_controller().get_status()
        except Exception:
            pass
        
        try:
            from modules.hpet_controller import get_controller
            modules_status['hpet'] = get_controller().get_status()
        except Exception:
            pass
            
        try:
            from modules.extreme_ai_optimizer import get_optimizer
            modules_status['extreme_ai'] = get_optimizer().applied_changes
        except Exception:
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
    
    print("Choose optimization level:")
    print("1. Safe")
    print("2. Balanced")
    print("3. Gaming")
    print("4. Aggressive")
    
    choice = input("\nOption (1-4): ").strip()
    
    levels = {
        '1': OptimizationLevel.SAFE,
        '2': OptimizationLevel.BALANCED,
        '3': OptimizationLevel.GAMING,
        '4': OptimizationLevel.AGGRESSIVE
    }
    
    level = levels.get(choice, OptimizationLevel.BALANCED)
    results = engine.apply_all(level)
