"""
NovaPulse System Tray Icon
Permite controlar o otimizador pela bandeja do sistema
Requer: pip install pystray pillow

FEATURE: Minimize-to-Tray automático
- Ao minimizar a janela, ela vai automaticamente para a bandeja
- Clique no ícone para restaurar
"""
import threading
import sys
import os
import ctypes
import time

# Tenta importar pystray (pode não estar instalado)
TRAY_AVAILABLE = False
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    print("[TRAY] pystray não instalado. Execute: pip install pystray pillow")

# Windows API Constants
SW_HIDE = 0
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9
GWL_STYLE = -16
WS_MINIMIZE = 0x20000000

# Windows API para esconder/mostrar janela
def get_console_window():
    """Retorna handle da janela do console"""
    return ctypes.windll.kernel32.GetConsoleWindow()

def is_window_minimized(hwnd):
    """Verifica se a janela está minimizada"""
    if not hwnd:
        return False
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    return bool(style & WS_MINIMIZE)

def hide_console():
    """Esconde a janela do console (vai para tray)"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)

def show_console():
    """Mostra a janela do console"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
        ctypes.windll.user32.SetForegroundWindow(hwnd)

class SystemTrayIcon:
    """Gerencia ícone na bandeja do sistema com mini-dashboard"""
    
    def __init__(self, optimizer_services=None, on_quit_callback=None):
        self.services = optimizer_services or {}
        self.on_quit = on_quit_callback
        self.icon = None
        self.running = False
        self.console_visible = True
        self.tooltip_thread = None
        self.minimize_monitor_thread = None
        self._last_minimize_state = False
        
        if not TRAY_AVAILABLE:
            print("[TRAY] Sistema de tray não disponível")
            return
    
    def _minimize_to_tray_monitor(self):
        """Monitora se a janela foi minimizada e esconde automaticamente para tray"""
        hwnd = get_console_window()
        while self.running and hwnd:
            try:
                is_minimized = is_window_minimized(hwnd)
                
                # Detecta transição para minimizado
                if is_minimized and not self._last_minimize_state and self.console_visible:
                    # Janela foi minimizada - esconde para tray
                    time.sleep(0.1)  # Pequeno delay para animação
                    hide_console()
                    self.console_visible = False
                    
                self._last_minimize_state = is_minimized
                
            except Exception:
                pass
            
            time.sleep(0.2)  # Checks every 200ms
    
    def _create_icon_image(self, mode='normal'):
        """Cria imagem do ícone baseado no modo"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Cores baseadas no modo
        mode_colors = {
            'boost': (255, 100, 50, 255),   # Laranja/Vermelho
            'normal': (0, 200, 80, 255),    # Verde
            'eco': (50, 180, 120, 255)      # Verde claro
        }
        fill_color = mode_colors.get(mode.lower(), mode_colors['normal'])
        
        # Desenha círculo
        margin = 4
        draw.ellipse([margin, margin, size-margin, size-margin], fill=fill_color)
        
        # Adiciona borda
        draw.ellipse([margin, margin, size-margin, size-margin], outline=(255, 255, 255, 200), width=2)
        
        return image
    
    def _get_mini_dashboard(self):
        """Gera texto do mini-dashboard para tooltip"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent()
            
            # RAM
            mem = psutil.virtual_memory()
            ram_used_gb = mem.used / (1024**3)
            ram_total_gb = mem.total / (1024**3)
            ram_percent = mem.percent
            
            # GPU NVIDIA
            gpu_percent = 0
            gpu_temp = 0
            gpu_name = ""
            try:
                import pynvml
                pynvml.nvmlInit()
                if pynvml.nvmlDeviceGetCount() > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_percent = util.gpu
                    gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, 0)
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')
                    gpu_name = name.replace("NVIDIA ", "").replace(" Laptop GPU", "")[:15]
            except:
                pass
            
            # Modo atual
            mode = "NORMAL"
            mode_icon = "🔄"
            if 'auto_profiler' in self.services:
                profiler = self.services['auto_profiler']
                mode = profiler.get_current_mode().value.upper()
                if mode == "BOOST":
                    mode_icon = "⚡"
                elif mode == "ECO":
                    mode_icon = "🌿"
            
            # Monta tooltip
            tooltip = f"⚡ NovaPulse 2.0\n"
            tooltip += f"━━━━━━━━━━━━━\n"
            tooltip += f"{mode_icon} Modo: {mode}\n"
            tooltip += f"🖥️ CPU: {cpu_percent:.0f}%\n"
            tooltip += f"💾 RAM: {ram_used_gb:.1f}/{ram_total_gb:.1f}GB ({ram_percent:.0f}%)\n"
            
            # GPU info
            if gpu_name:
                tooltip += f"🎮 GPU: {gpu_name}\n"
                tooltip += f"   Load: {gpu_percent}% | Temp: {gpu_temp}°C"
            
            return tooltip, mode.lower()
            
        except Exception as e:
            return f"⚡ NovaPulse 2.0\n[Erro: {e}]", "normal"
    
    def _tooltip_update_loop(self):
        """Atualiza tooltip a cada 2 segundos"""
        import time
        while self.running and self.icon:
            try:
                tooltip, mode = self._get_mini_dashboard()
                self.icon.title = tooltip
                self.icon.icon = self._create_icon_image(mode)
            except:
                pass
            time.sleep(2)
    
    def _create_menu(self):
        """Cria menu de contexto do tray"""
        menu_items = [
            pystray.MenuItem('⚡ NovaPulse', None, enabled=False),
            pystray.Menu.SEPARATOR,
            
            # Controles principais
            pystray.MenuItem('📺 Mostrar Dashboard', self._toggle_console, default=True),
            pystray.Menu.SEPARATOR,
            
            # Controle de modo
            pystray.MenuItem('🎛️ Modo', pystray.Menu(
                pystray.MenuItem('🚀 Forçar BOOST', lambda: self._force_mode('boost')),
                pystray.MenuItem('🔄 Modo AUTO', lambda: self._force_mode('auto')),
                pystray.MenuItem('🌿 Forçar ECO', lambda: self._force_mode('eco')),
            )),
            
            # Ações rápidas
            pystray.MenuItem('🧹 Limpar RAM', self._force_clean),
            pystray.Menu.SEPARATOR,
            
            # Sair
            pystray.MenuItem('❌ Sair', self._quit)
        ]
        return pystray.Menu(*menu_items)
    
    def _toggle_console(self):
        """Alterna visibilidade do console (Mostrar/Esconder)"""
        if self.console_visible:
            hide_console()
            self.console_visible = False
        else:
            show_console()
            self.console_visible = True
            self._last_minimize_state = False  # Reset minimize state
    
    def _force_mode(self, mode_name):
        """Força um modo específico via menu"""
        try:
            from modules.auto_profiler import get_profiler, SystemMode
            profiler = get_profiler()
            
            if mode_name == 'boost':
                profiler.force_mode(SystemMode.BOOST)
            elif mode_name == 'eco':
                profiler.force_mode(SystemMode.ECO)
            else:
                profiler.force_mode(SystemMode.NORMAL)
                
        except Exception as e:
            print(f"[TRAY] Erro ao mudar modo: {e}")
    
    def _force_clean(self):
        """Força limpeza de RAM"""
        if 'cleaner' in self.services:
            freed = self.services['cleaner'].clean_standby_memory()
            print(f"[TRAY] Limpeza manual: {freed}MB liberados")
    
    def _quit(self):
        """Fecha o programa"""
        self.running = False
        show_console()
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()
        sys.exit(0)
    
    def start(self):
        """Inicia o ícone na bandeja"""
        if not TRAY_AVAILABLE:
            print("[TRAY] Tray não disponível - continuando sem ícone")
            return False
        
        self.running = True
        
        try:
            tooltip, mode = self._get_mini_dashboard()
            
            self.icon = pystray.Icon(
                name="NovaPulse",
                icon=self._create_icon_image(mode),
                title=tooltip,
                menu=self._create_menu()
            )
            
            # Thread para atualizar tooltip
            self.tooltip_thread = threading.Thread(target=self._tooltip_update_loop, daemon=True)
            self.tooltip_thread.start()
            
            # Thread para monitorar minimize-to-tray
            self.minimize_monitor_thread = threading.Thread(target=self._minimize_to_tray_monitor, daemon=True)
            self.minimize_monitor_thread.start()
            
            # Roda em thread separada
            tray_thread = threading.Thread(target=self.icon.run, daemon=True)
            tray_thread.start()
            
            print("[TRAY] ✓ Ícone na bandeja ativado")
            print("[TRAY] → Minimize: Vai para bandeja | Clique no ícone: Restaurar")
            return True
            
        except Exception as e:
            print(f"[TRAY] Erro ao iniciar tray: {e}")
            return False
    
    def stop(self):
        """Para o ícone"""
        self.running = False
        show_console()
        if self.icon:
            self.icon.stop()


if __name__ == "__main__":
    # Teste
    def on_quit():
        print("Saindo...")
        sys.exit(0)
    
    tray = SystemTrayIcon(on_quit_callback=on_quit)
    if tray.start():
        print("Tray iniciado. Clique com botão direito no ícone.")
        print("Clique em 'Mostrar/Esconder' para minimizar para bandeja.")
        try:
            while tray.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            tray.stop()
    else:
        print("Falha ao iniciar tray. Instale: pip install pystray pillow")
