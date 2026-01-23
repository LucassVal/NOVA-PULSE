"""
NovaPulse Dashboard WebView
Interface HTML moderna integrada via PyWebView
"""
import threading
import os
import sys

# Tenta importar pywebview
WEBVIEW_AVAILABLE = False
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    print("[DASHBOARD] pywebview não instalado. Execute: pip install pywebview")

# Importa módulos do sistema
try:
    import psutil
except ImportError:
    psutil = None


class DashboardAPI:
    """API exposta para o JavaScript do dashboard"""
    
    def __init__(self, services=None):
        self.services = services or {}
        self.window = None
    
    def set_window(self, window):
        """Define referência à janela"""
        self.window = window
    
    def get_metrics(self):
        """Retorna métricas do sistema em tempo real"""
        if not psutil:
            return None
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent()
            cpu_cores = psutil.cpu_count()
            
            # RAM
            mem = psutil.virtual_memory()
            ram_percent = mem.percent
            ram_used_gb = mem.used / (1024**3)
            ram_total_gb = mem.total / (1024**3)
            
            # GPU (via pynvml se disponível)
            gpu_percent = None
            gpu_name = None
            gpu_mem_mb = 0
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode('utf-8')
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_percent = util.gpu
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_mem_mb = int(mem_info.used / (1024**2))
            except:
                pass
            
            # Temperatura CPU
            cpu_temp = 0
            try:
                if 'temp_service' in self.services:
                    cpu_temp = self.services['temp_service'].get_cpu_temp() or 0
                else:
                    # Fallback via WMI
                    import wmi
                    w = wmi.WMI(namespace="root\\wmi")
                    temps = w.MSAcpi_ThermalZoneTemperature()
                    if temps:
                        cpu_temp = int((temps[0].CurrentTemperature / 10) - 273.15)
            except:
                cpu_temp = 45  # Fallback
            
            # Modo atual
            mode = "NORMAL"
            if 'auto_profiler' in self.services:
                try:
                    mode = self.services['auto_profiler'].get_current_mode().value
                except:
                    pass
            
            return {
                'cpu_percent': int(cpu_percent),
                'cpu_cores': cpu_cores,
                'ram_percent': int(ram_percent),
                'ram_used_gb': ram_used_gb,
                'ram_total_gb': ram_total_gb,
                'gpu_percent': gpu_percent,
                'gpu_name': gpu_name,
                'gpu_mem_mb': gpu_mem_mb,
                'cpu_temp': cpu_temp,
                'mode': mode
            }
            
        except Exception as e:
            print(f"[DASHBOARD] Erro ao obter métricas: {e}")
            return None
    
    def force_boost(self):
        """Força modo BOOST"""
        try:
            from modules.auto_profiler import get_profiler, SystemMode
            profiler = get_profiler()
            profiler.force_mode(SystemMode.BOOST)
            return True
        except Exception as e:
            print(f"[DASHBOARD] Erro ao forçar BOOST: {e}")
            return False
    
    def force_eco(self):
        """Força modo ECO"""
        try:
            from modules.auto_profiler import get_profiler, SystemMode
            profiler = get_profiler()
            profiler.force_mode(SystemMode.ECO)
            return True
        except Exception as e:
            print(f"[DASHBOARD] Erro ao forçar ECO: {e}")
            return False
    
    def force_auto(self):
        """Retorna ao modo AUTO (NORMAL)"""
        try:
            from modules.auto_profiler import get_profiler, SystemMode
            profiler = get_profiler()
            profiler.force_mode(SystemMode.NORMAL)
            return True
        except Exception as e:
            print(f"[DASHBOARD] Erro ao forçar AUTO: {e}")
            return False
    
    def clean_ram(self):
        """Força limpeza de RAM"""
        try:
            if 'cleaner' in self.services:
                freed = self.services['cleaner'].clean_standby_memory()
                return {'success': True, 'freed_mb': freed}
            return {'success': False, 'error': 'Cleaner não disponível'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def minimize_to_tray(self):
        """Minimiza para a bandeja"""
        if self.window:
            self.window.minimize()
        return True


class DashboardWebView:
    """Gerenciador do dashboard HTML via PyWebView"""
    
    def __init__(self, services=None):
        self.services = services or {}
        self.api = DashboardAPI(services)
        self.window = None
        self.running = False
    
    def _get_html_path(self):
        """Retorna caminho do arquivo HTML"""
        # Tenta encontrar o HTML no mesmo diretório
        if getattr(sys, 'frozen', False):
            # Executando como exe
            base_path = sys._MEIPASS
        else:
            # Executando como script
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Se estiver em modules/, sobe um nível
            if base_path.endswith('modules'):
                base_path = os.path.dirname(base_path)
        
        html_path = os.path.join(base_path, 'dashboard.html')
        
        if os.path.exists(html_path):
            return html_path
        
        # Fallback para o diretório atual
        return os.path.join(os.getcwd(), 'dashboard.html')
    
    def start(self):
        """Inicia o dashboard em uma nova janela"""
        if not WEBVIEW_AVAILABLE:
            print("[DASHBOARD] PyWebView não disponível - usando dashboard de console")
            return False
        
        html_path = self._get_html_path()
        
        if not os.path.exists(html_path):
            print(f"[DASHBOARD] HTML não encontrado: {html_path}")
            return False
        
        self.running = True
        
        try:
            # Cria janela
            self.window = webview.create_window(
                title='NovaPulse Dashboard',
                url=html_path,
                width=900,
                height=700,
                min_size=(600, 500),
                js_api=self.api,
                background_color='#0a0a0f'
            )
            
            self.api.set_window(self.window)
            
            print("[DASHBOARD] ✓ Dashboard HTML iniciado")
            return True
            
        except Exception as e:
            print(f"[DASHBOARD] Erro ao iniciar: {e}")
            return False
    
    def run_blocking(self):
        """Inicia o webview de forma bloqueante (deve ser chamado da thread principal)"""
        if not WEBVIEW_AVAILABLE:
            return False
        
        if self.start():
            webview.start()
            return True
        return False
    
    def stop(self):
        """Para o dashboard"""
        self.running = False
        if self.window:
            try:
                self.window.destroy()
            except:
                pass


def create_dashboard(services=None):
    """Factory function para criar dashboard"""
    return DashboardWebView(services)


if __name__ == "__main__":
    # Teste standalone
    dashboard = DashboardWebView()
    dashboard.run_blocking()
