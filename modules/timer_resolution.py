"""
Timer Resolution Optimizer
Força resolução de timer para 0.5ms (melhor input lag)
"""
import ctypes
import threading
import time

class TimerResolutionOptimizer:
    """Otimiza resolução do timer do Windows para baixa latência"""
    
    def __init__(self):
        self.ntdll = ctypes.WinDLL('ntdll')
        self.running = False
        self.thread = None
        self.original_resolution = None
        
        # Target: 0.5ms (5000 * 100ns = 0.5ms)
        self.target_resolution = 5000  # 100-nanosecond units
    
    def get_current_resolution(self):
        """Retorna resolução atual do timer em ms"""
        try:
            current = ctypes.c_ulong()
            minimum = ctypes.c_ulong()
            maximum = ctypes.c_ulong()
            
            self.ntdll.NtQueryTimerResolution(
                ctypes.byref(minimum),
                ctypes.byref(maximum),
                ctypes.byref(current)
            )
            
            return current.value / 10000  # Converte para ms
        except:
            return 15.625  # Default Windows
    
    def set_resolution(self, resolution_100ns):
        """Define resolução do timer (em unidades de 100ns)"""
        try:
            actual = ctypes.c_ulong()
            
            # NtSetTimerResolution(DesiredResolution, SetResolution, ActualResolution)
            result = self.ntdll.NtSetTimerResolution(
                ctypes.c_ulong(resolution_100ns),
                ctypes.c_bool(True),
                ctypes.byref(actual)
            )
            
            if result == 0:  # STATUS_SUCCESS
                return actual.value / 10000  # Retorna em ms
            return None
        except Exception as e:
            print(f"[TIMER] Erro: {e}")
            return None
    
    def apply_optimization(self):
        """Aplica otimização de timer (0.5ms)"""
        print("[TIMER] Aplicando resolução de timer para 0.5ms...")
        
        # Salva resolução original
        self.original_resolution = self.get_current_resolution()
        print(f"[TIMER] Resolução original: {self.original_resolution:.3f}ms")
        
        # Aplica nova resolução
        actual = self.set_resolution(self.target_resolution)
        
        if actual:
            print(f"[TIMER] ✓ Nova resolução: {actual:.3f}ms")
            print(f"[TIMER] ✓ Melhoria: -{(self.original_resolution - actual):.2f}ms input lag")
            return True
        else:
            print("[TIMER] ⚠ Não foi possível alterar resolução")
            return False
    
    def start_persistent(self):
        """Mantém resolução baixa persistentemente (alguns apps resetam)"""
        self.running = True
        
        def maintain_loop():
            while self.running:
                self.set_resolution(self.target_resolution)
                time.sleep(60)  # Re-aplica a cada 60 segundos
        
        self.thread = threading.Thread(target=maintain_loop, daemon=True)
        self.thread.start()
    
    def restore(self):
        """Restaura resolução padrão"""
        self.running = False
        if self.original_resolution:
            # 156250 = 15.625ms (padrão Windows)
            self.set_resolution(156250)
            print("[TIMER] Resolução restaurada para padrão")


if __name__ == "__main__":
    timer = TimerResolutionOptimizer()
    print(f"Resolução atual: {timer.get_current_resolution():.3f}ms")
    
    timer.apply_optimization()
    
    input("Pressione ENTER para restaurar...")
    timer.restore()
