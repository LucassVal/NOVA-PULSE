"""
NovaPulse System Tray Icon
Controls the optimizer from the system tray
Requires: pip install pystray pillow

FEATURE: Automatic minimize-to-tray
- When minimizing the window, it goes automatically to the tray
- Click the icon to restore
"""
import threading
import sys
import os
import ctypes
import time

# Try to import pystray (may not be installed)
TRAY_AVAILABLE = False
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    print("[TRAY] pystray not installed. Run: pip install pystray pillow")

# Windows API Constants
SW_HIDE = 0
SW_SHOW = 5
SW_MINIMIZE = 6
SW_RESTORE = 9
GWL_STYLE = -16
WS_MINIMIZE = 0x20000000

# Windows API to hide/show window
def get_console_window():
    """Returns console window handle"""
    return ctypes.windll.kernel32.GetConsoleWindow()

def is_window_minimized(hwnd):
    """Check if window is minimized"""
    if not hwnd:
        return False
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    return bool(style & WS_MINIMIZE)

def hide_console():
    """Hide console window (go to tray)"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)

def show_console():
    """Show console window"""
    hwnd = get_console_window()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
        ctypes.windll.user32.SetForegroundWindow(hwnd)

class SystemTrayIcon:
    """Manages system tray icon with mini-dashboard"""
    
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
            print("[TRAY] Tray system not available")
            return
    
    def _minimize_to_tray_monitor(self):
        """Monitor if window was minimized and auto-hide to tray"""
        hwnd = get_console_window()
        while self.running and hwnd:
            try:
                is_minimized = is_window_minimized(hwnd)
                # Detect transition to minimized
                if is_minimized and not self._last_minimize_state and self.console_visible:
                    # Window was minimized - hide to tray
                    time.sleep(0.1)  # Small delay for animation
                    hide_console()
                    self.console_visible = False
                self._last_minimize_state = is_minimized
            except Exception:
                pass
            time.sleep(0.2)  # Checks every 200ms
    
    def _create_icon_image(self, mode='normal'):
        """Create icon image based on mode"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        mode_colors = {
            'boost': (255, 100, 50, 255),
            'normal': (0, 200, 80, 255),
            'eco': (50, 180, 120, 255)
        }
        fill_color = mode_colors.get(mode.lower(), mode_colors['normal'])
        margin = 4
        draw.ellipse([margin, margin, size-margin, size-margin], fill=fill_color)
        draw.ellipse([margin, margin, size-margin, size-margin], outline=(255, 255, 255, 200), width=2)
        return image
    
    def _get_mini_dashboard(self):
        """Generate mini-dashboard text for tooltip (max 128 chars)"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            ram_pct = mem.percent
            gpu_pct = 0
            gpu_temp = 0
            try:
                import pynvml
                pynvml.nvmlInit()
                if pynvml.nvmlDeviceGetCount() > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_pct = util.gpu
                    gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, 0)
            except:
                pass
            mode = "NORMAL"
            if 'auto_profiler' in self.services:
                try:
                    mode = self.services['auto_profiler'].get_current_mode().value.upper()
                except:
                    pass
            tooltip = f"NovaPulse 2.2.1 | {mode}\n"
            tooltip += f"CPU:{cpu_percent:.0f}% RAM:{ram_pct:.0f}%\n"
            tooltip += f"GPU:{gpu_pct}% {gpu_temp}C"
            return tooltip, mode.lower()
        except Exception as e:
            return "NovaPulse 2.2.1", "normal"
    
    def _tooltip_update_loop(self):
        """Update tooltip every 2 seconds"""
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
        """Create tray context menu"""
        menu_items = [
            pystray.MenuItem('⚡ NovaPulse', None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('📺 Show Dashboard', self._toggle_console, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('🏛️ Mode', pystray.Menu(
                pystray.MenuItem('⚡ Force ACTIVE', lambda: self._force_mode('active')),
                pystray.MenuItem('🌿 Force IDLE', lambda: self._force_mode('idle')),
            )),
            pystray.MenuItem('🧹 Clean RAM', self._force_clean),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('❌ Exit', self._quit)
        ]
        return pystray.Menu(*menu_items)
    
    def _toggle_console(self):
        """Toggle console visibility (Show/Hide)"""
        if self.console_visible:
            hide_console()
            self.console_visible = False
        else:
            show_console()
            self.console_visible = True
            self._last_minimize_state = False
    
    def _force_mode(self, mode_name):
        """Force a specific mode via tray menu."""
        try:
            from modules.auto_profiler import get_profiler, SystemMode
            profiler = get_profiler()
            if mode_name == 'active':
                profiler.force_mode(SystemMode.ACTIVE)
            elif mode_name == 'idle':
                profiler.force_mode(SystemMode.IDLE)
        except Exception as e:
            print(f"[TRAY] Error changing mode: {e}")
    
    def _force_clean(self):
        """Force RAM cleanup"""
        if 'cleaner' in self.services:
            freed = self.services['cleaner'].clean_standby_memory()
            print(f"[TRAY] Manual cleanup: {freed}MB freed")
    
    def _quit(self):
        """Close the program"""
        self.running = False
        show_console()
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()
        sys.exit(0)
    
    def start(self):
        """Start the tray icon"""
        if not TRAY_AVAILABLE:
            print("[TRAY] Tray not available - continuing without icon")
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
            # Thread to update tooltip
            self.tooltip_thread = threading.Thread(target=self._tooltip_update_loop, daemon=True)
            self.tooltip_thread.start()
            # Thread to monitor minimize-to-tray
            self.minimize_monitor_thread = threading.Thread(target=self._minimize_to_tray_monitor, daemon=True)
            self.minimize_monitor_thread.start()
            # Run in separate thread
            tray_thread = threading.Thread(target=self.icon.run, daemon=True)
            tray_thread.start()
            print("[TRAY] ✓ Tray icon activated")
            print("[TRAY] → Minimize: Goes to tray | Click icon: Restore")
            return True
        except Exception as e:
            print(f"[TRAY] Error starting tray: {e}")
            return False
    
    def stop(self):
        """Stop the icon"""
        self.running = False
        show_console()
        if self.icon:
            self.icon.stop()


if __name__ == "__main__":
    def on_quit():
        print("Exiting...")
        sys.exit(0)
    
    tray = SystemTrayIcon(on_quit_callback=on_quit)
    if tray.start():
        print("Tray started. Right-click the icon.")
        print("Click 'Show/Hide' to minimize to tray.")
        try:
            while tray.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            tray.stop()
    else:
        print("Failed to start tray. Install: pip install pystray pillow")
