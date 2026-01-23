"""
NovaPulse Auto-Profiler
Sistema inteligente de ajuste automático baseado em carga do sistema
Substitui perfis estáticos por detecção em tempo real
"""
import threading
import time
import psutil
from enum import Enum
from collections import deque


class SystemMode(Enum):
    """Modos de operação do sistema"""
    BOOST = "boost"      # Máxima performance (CPU > 85%)
    NORMAL = "normal"    # Operação padrão
    ECO = "eco"          # Economia de energia (CPU < 30%)


class AutoProfiler:
    """
    Profiler automático que ajusta o sistema em tempo real.
    
    Lógica:
    - CPU > 85% por 2s → BOOST MODE
    - CPU < 30% por 5s → ECO MODE
    - Caso contrário → NORMAL MODE
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self.thread = None
        
        # Configurações
        self.check_interval = self.config.get('check_interval', 2)  # 2 segundos
        self.boost_threshold = self.config.get('boost_threshold', 85)  # CPU > 85%
        self.eco_threshold = self.config.get('eco_threshold', 30)  # CPU < 30%
        self.boost_hold_time = self.config.get('boost_hold_time', 5)  # 5s para ativar boost
        self.eco_hold_time = self.config.get('eco_hold_time', 5)  # 5s para ativar eco
        
        # ECO Progressivo - reduz gradualmente até min_cpu_percent
        self.eco_progressive = self.config.get('eco_progressive', True)
        self.min_cpu_percent = self.config.get('min_cpu_percent', 10)  # Mínimo 10%
        self.current_eco_level = 70  # Nível atual do ECO (começa em 70%, vai até 10%)
        
        # Thermal Throttle - reduz CPU quando temperatura alta
        self.thermal_throttle_enabled = self.config.get('thermal_throttle_enabled', True)
        self.thermal_threshold = self.config.get('thermal_threshold', 90)  # 90°C
        self.thermal_throttle_percent = self.config.get('thermal_throttle_percent', 80)  # Reduz para 80%
        self.thermal_throttle_active = False
        
        # Estado atual
        self.current_mode = SystemMode.NORMAL
        self.previous_mode = SystemMode.NORMAL
        
        # Histórico de CPU para suavização
        self.cpu_history = deque(maxlen=10)  # Últimas 10 leituras
        
        # Contadores de tempo em cada estado
        self.high_cpu_counter = 0
        self.low_cpu_counter = 0
        
        # Referência aos serviços do otimizador
        self.services = {}
        
        # Callbacks para mudança de modo
        self.on_mode_change_callbacks = []
        
    def set_services(self, services: dict):
        """Define referência aos serviços do otimizador"""
        self.services = services
        
    def add_mode_change_callback(self, callback):
        """Adiciona callback para quando o modo mudar"""
        self.on_mode_change_callbacks.append(callback)
        
    def get_current_mode(self) -> SystemMode:
        """Retorna modo atual"""
        return self.current_mode
    
    def get_mode_name(self) -> str:
        """Retorna nome amigável do modo"""
        names = {
            SystemMode.BOOST: "⚡ BOOST",
            SystemMode.NORMAL: "🔄 NORMAL", 
            SystemMode.ECO: "🌿 ECO"
        }
        return names.get(self.current_mode, "NORMAL")
    
    def get_avg_cpu(self) -> float:
        """Retorna média de CPU das últimas leituras"""
        if not self.cpu_history:
            return 0.0
        return sum(self.cpu_history) / len(self.cpu_history)
    
    def start(self):
        """Inicia monitoramento automático"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
        print(f"[AUTO] NovaPulse Auto-Profiler iniciado")
        print(f"[AUTO] → BOOST: CPU > {self.boost_threshold}% por {self.boost_hold_time}s")
        print(f"[AUTO] → ECO: CPU < {self.eco_threshold}% por {self.eco_hold_time}s")
        print(f"[AUTO] → Verificação a cada {self.check_interval}s")
        
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[AUTO] Auto-Profiler parado")
        
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                # Lê CPU atual
                cpu_percent = psutil.cpu_percent(interval=0.5)
                self.cpu_history.append(cpu_percent)
                
                # Calcula média para suavização
                avg_cpu = self.get_avg_cpu()
                
                # === THERMAL THROTTLE ===
                if self.thermal_throttle_enabled:
                    self._check_thermal_throttle()
                
                # Lógica de detecção de modo
                new_mode = self._determine_mode(avg_cpu)
                
                # Se modo mudou, aplica configurações
                if new_mode != self.current_mode:
                    self._apply_mode(new_mode)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"[AUTO] Erro no monitoramento: {e}")
                time.sleep(5)
    
    def _check_thermal_throttle(self):
        """Verifica temperatura e aplica throttle se necessário"""
        try:
            cpu_temp = self._get_cpu_temp()
            
            if cpu_temp >= self.thermal_threshold:
                # Temperatura alta - ativa throttle
                if not self.thermal_throttle_active:
                    self.thermal_throttle_active = True
                    print(f"\n[THERMAL] ⚠️ CPU {cpu_temp}°C >= {self.thermal_threshold}°C")
                    print(f"[THERMAL] 🌡️ Ativando Thermal Throttle → {self.thermal_throttle_percent}% CPU")
                    self._apply_thermal_limit(self.thermal_throttle_percent)
                    
            elif self.thermal_throttle_active and cpu_temp < (self.thermal_threshold - 5):
                # Temperatura voltou ao normal (com histerese de 5°C)
                self.thermal_throttle_active = False
                print(f"\n[THERMAL] ✓ CPU {cpu_temp}°C - Temperatura normalizada")
                print(f"[THERMAL] Restaurando limite normal → 85% CPU")
                self._apply_thermal_limit(85)  # Volta ao limite normal
                
        except Exception as e:
            pass  # Silently ignore thermal read errors
    
    def _get_cpu_temp(self) -> int:
        """Obtém temperatura da CPU"""
        try:
            if 'temp_service' in self.services:
                return self.services['temp_service'].get_cpu_temp() or 0
            else:
                # Fallback via WMI
                import wmi
                w = wmi.WMI(namespace="root\\wmi")
                temps = w.MSAcpi_ThermalZoneTemperature()
                if temps:
                    return int((temps[0].CurrentTemperature / 10) - 273.15)
        except:
            pass
        return 50  # Default se não conseguir ler
    
    def _apply_thermal_limit(self, percent: int):
        """Aplica limite de CPU para thermal throttle"""
        try:
            if 'cpu_power' in self.services:
                self.services['cpu_power'].set_max_frequency(percent)
        except Exception as e:
            print(f"[THERMAL] Erro ao aplicar limite: {e}")
    
    def _determine_mode(self, avg_cpu: float) -> SystemMode:
        """Determina qual modo baseado na carga de CPU"""
        
        # Verifica se deve entrar em BOOST
        if avg_cpu > self.boost_threshold:
            self.high_cpu_counter += 1
            self.low_cpu_counter = 0
            
            # Precisa manter alta por X segundos
            if self.high_cpu_counter >= (self.boost_hold_time / self.check_interval):
                return SystemMode.BOOST
                
        # Verifica se deve entrar em ECO
        elif avg_cpu < self.eco_threshold:
            self.low_cpu_counter += 1
            self.high_cpu_counter = 0
            
            # Precisa manter baixa por X segundos
            if self.low_cpu_counter >= (self.eco_hold_time / self.check_interval):
                return SystemMode.ECO
                
        # Reset contadores se CPU está no meio
        else:
            self.high_cpu_counter = 0
            self.low_cpu_counter = 0
            
            # Se estava em BOOST ou ECO, volta para NORMAL
            if self.current_mode != SystemMode.NORMAL:
                return SystemMode.NORMAL
        
        # Mantém modo atual
        return self.current_mode
    
    def _apply_mode(self, new_mode: SystemMode):
        """Aplica configurações do novo modo"""
        self.previous_mode = self.current_mode
        self.current_mode = new_mode
        
        print(f"\n[AUTO] 🔄 Mudança de modo: {self.previous_mode.value.upper()} → {new_mode.value.upper()}")
        
        try:
            if new_mode == SystemMode.BOOST:
                self._apply_boost_mode()
            elif new_mode == SystemMode.ECO:
                self._apply_eco_mode()
            else:
                self._apply_normal_mode()
                
            # Notifica callbacks
            for callback in self.on_mode_change_callbacks:
                try:
                    callback(new_mode)
                except:
                    pass
                    
        except Exception as e:
            print(f"[AUTO] Erro ao aplicar modo: {e}")
    
    def _apply_boost_mode(self):
        """Aplica configurações de BOOST (máxima performance)"""
        print("[AUTO] ⚡ BOOST MODE ATIVADO - Máxima Performance!")
        
        # CPU: 100%
        if 'cpu_power' in self.services:
            self.services['cpu_power'].set_max_cpu_frequency(100)
            
        # RAM: Limpa agressivamente
        if 'cleaner' in self.services:
            self.services['cleaner'].threshold_mb = 2048  # 2GB
            self.services['cleaner'].check_interval = 2
            # Força uma limpeza imediata
            self.services['cleaner'].clean_standby_memory()
            
    def _apply_eco_mode(self):
        """Aplica configurações de ECO (economia progressiva)"""
        if self.eco_progressive:
            # ECO Progressivo: reduz gradualmente
            # Primeira ativação: 70%
            # Continua em ECO: reduz 10% a cada ciclo até min_cpu_percent
            if self.previous_mode != SystemMode.ECO:
                # Primeira vez entrando em ECO
                self.current_eco_level = 70
            else:
                # Já estava em ECO, reduz mais
                self.current_eco_level = max(self.min_cpu_percent, self.current_eco_level - 10)
            
            print(f"[AUTO] 🌿 ECO MODE PROGRESSIVO - CPU: {self.current_eco_level}%")
            
            if 'cpu_power' in self.services:
                self.services['cpu_power'].set_max_cpu_frequency(self.current_eco_level)
        else:
            # ECO simples (70% fixo)
            print("[AUTO] 🌿 ECO MODE ATIVADO - Economia de Energia")
            if 'cpu_power' in self.services:
                self.services['cpu_power'].set_max_cpu_frequency(70)
            
        # RAM: Menos agressivo
        if 'cleaner' in self.services:
            self.services['cleaner'].threshold_mb = 8192  # 8GB
            self.services['cleaner'].check_interval = 30
            
    def _apply_normal_mode(self):
        """Aplica configurações de NORMAL (balanceado)"""
        print("[AUTO] 🔄 NORMAL MODE - Operação Balanceada")
        
        # CPU: 85% (permite turbo mas com limite térmico)
        if 'cpu_power' in self.services:
            self.services['cpu_power'].set_max_cpu_frequency(85)
            
        # RAM: Moderado
        if 'cleaner' in self.services:
            self.services['cleaner'].threshold_mb = 4096  # 4GB
            self.services['cleaner'].check_interval = 5
    
    def force_mode(self, mode: SystemMode):
        """Força um modo específico (override manual)"""
        print(f"[AUTO] Modo forçado manualmente: {mode.value.upper()}")
        self._apply_mode(mode)
        # Reset contadores
        self.high_cpu_counter = 0
        self.low_cpu_counter = 0


# Singleton global
_instance = None

def get_profiler() -> AutoProfiler:
    """Retorna instância singleton do AutoProfiler"""
    global _instance
    if _instance is None:
        _instance = AutoProfiler()
    return _instance


if __name__ == "__main__":
    # Teste standalone
    profiler = AutoProfiler()
    profiler.start()
    
    print("\nMonitorando sistema...")
    print("Pressione Ctrl+C para parar\n")
    
    try:
        while True:
            mode = profiler.get_mode_name()
            avg_cpu = profiler.get_avg_cpu()
            print(f"\r[{mode}] CPU Média: {avg_cpu:.1f}%  ", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        profiler.stop()
        print("\n[INFO] Finalizado")
