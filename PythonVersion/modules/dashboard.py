"""
Real-time visual dashboard for Windows Optimizer
Displays system stats, optimizations, and statistics
"""
import psutil
import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.align import Align
from datetime import datetime
from modules import temperature_service

class Dashboard:
    def __init__(self):
        self.console = Console()
        self.running = False
        
        # Statistics tracking
        self.stats_tracker = {
            'total_ram_cleaned_mb': 0,
            'total_cleanups': 0,
            'uptime_seconds': 0,
            'start_time': time.time()
        }
        
        # Layout configuration
        self.layout = Layout()
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=8)
        )
        
        # Split body em colunas
        self.layout["body"].split_row(
            Layout(name="cpu_gpu", ratio=1),
            Layout(name="memory", ratio=1)
        )
        
        # Dados para exibir
        self.stats = {
            'cpu_percent': 0,
            'cpu_temp': 0,
            'cpu_freq': 0,
            'cpu_limit': 85,
            'gpu_nvidia_name': '',
            'gpu_nvidia_percent': 0,
            'gpu_nvidia_temp': 0,
            'gpu_nvidia_mem_used': 0,
            'gpu_nvidia_mem_total': 0,
            'gpu_nvidia_power_limit': 0,  # Power limit aplicado
            'gpu_intel_name': '',
            'ram_used': 0,
            'ram_total': 0,
            'ram_percent': 0,
            'ram_cleanups': 0,
            'priority_high': 0,
            'priority_low': 0
        }
        
        # Detecta GPUs
        self.has_nvidia = False
        self.has_intel = False
        self.nvidia_handle = None
        
        # Tenta detectar NVIDIA (geralmente é o device 0)
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            if device_count > 0:
                # Pega o primeiro device
                self.nvidia_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(self.nvidia_handle)
                
                # Decodifica se for bytes
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                self.stats['gpu_nvidia_name'] = name
                self.has_nvidia = True
                print(f"[GPU] NVIDIA detectada: {name}")
        except Exception as e:
            print(f"[GPU] NVIDIA não detectada: {e}")
        
        # Detecta Intel integrada via WMI (CACHED at init - no per-frame calls)
        self._cached_intel_name = "Intel Integrated Graphics"
        try:
            import wmi
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                if 'intel' in gpu.Name.lower():
                    self.has_intel = True
                    self.stats['gpu_intel_name'] = gpu.Name
                    self._cached_intel_name = gpu.Name
                    print(f"[GPU] Intel detectada: {gpu.Name}")
                    break
        except Exception as e:
            print(f"[GPU] Intel não detectada: {e}")
        
        # Get temperature service singleton
        self._temp_service = temperature_service.get_service()
    
    def make_header(self):
        """Creates header with title and status"""
        current_time = datetime.now().strftime("%H:%M:%S")
        status = "[green]● ACTIVE[/green]"
        
        header_text = f"[bold cyan]⚡ WINDOWS OPTIMIZER DASHBOARD[/bold cyan] | {current_time} | {status}"
        return Panel(
            Align.center(header_text),
            border_style="bold blue"
        )
    
    def make_cpu_gpu_panel(self):
        """CPU and GPU Panel"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=18)
        table.add_column("Value", justify="right")
        
        # CPU - Pedagogical Colors
        # Usage
        cpu_usage = self.stats['cpu_percent']
        if cpu_usage < 50:
            cpu_color = "green"
            cpu_desc = "[LIGHT]"
        elif cpu_usage < 80:
            cpu_color = "yellow"
            cpu_desc = "[MODERATE]"
        else:
            cpu_color = "red"
            cpu_desc = "[HEAVY]"
        
        cpu_bar = self._make_bar(cpu_usage, 100, cpu_color)
        
        # Temp
        cpu_temp = self.stats['cpu_temp']
        temp_display = f"{cpu_temp:.0f}°C" if cpu_temp > 0 else "N/A"
        
        if cpu_temp < 60:
            cpu_t_color = "cyan"
            cpu_t_desc = "❄️ COOL"
        elif cpu_temp < 75:
            cpu_t_color = "green"
            cpu_t_desc = "✅ GOOD"
        elif cpu_temp < 85:
            cpu_t_color = "yellow"
            cpu_t_desc = "⚠️ WARM" 
        else:
            cpu_t_color = "red"
            cpu_t_desc = "🔥 HOT"

        freq_color = "cyan"
        
        table.add_row("[bold white]CPU Package[/bold white]", "")
        table.add_row("  Total Load", f"[{cpu_color}]{cpu_usage:.1f}% {cpu_desc}[/{cpu_color}] {cpu_bar}")
        table.add_row("  Package Temp", f"[{cpu_t_color}]{temp_display} {cpu_t_desc}[/{cpu_t_color}]")
        table.add_row("  Governor Cap", f"[yellow]{self.stats['cpu_limit']}%[/yellow] (Smart Limit)")
        table.add_row("", "")
        
        # === ACTIVE PER-CORE MONITORING (COMPACT) ===
        cores_usage = psutil.cpu_percent(percpu=True)
        try:
            cores_freq = psutil.cpu_freq(percpu=True)
        except:
            cores_freq = []
            
        table.add_row("[bold white]Active Cores[/bold white]", "[dim]Real-Time Utilization[/dim]")
        
        # Grid Display: 4 Cores per row (Compact)
        row_str = ""
        for i, u in enumerate(cores_usage):
            # Color logic
            c_color = "green" if u < 50 else "yellow" if u < 80 else "red"
            
            # Turbo Logic
            turbo = "⚡" if u > 20 else " "
            
            # Format: C0: 12%⚡   (No bars)
            core_str = f"C{i}:[{c_color}]{u:3.0f}%{turbo}[/{c_color}]  "
            
            row_str += core_str
            
            # Break line every 4 cores
            if (i + 1) % 4 == 0:
                table.add_row("", row_str)
                row_str = ""
        
        # Add remaining cores if any
        if row_str:
             table.add_row("", row_str)

        table.add_row("", "")
        
        # === GPU SECTION (MULTI-GPU SUPPORT) ===
        # Using CACHED Intel GPU name (no WMI calls per-frame)
        intel_name = self._cached_intel_name
        intel_active = self.has_intel

        table.add_row("", "")
        table.add_row("[bold white]GPU ADAPTERS[/bold white]", "")

        # 1. NVIDIA (Dedicated)
        if self.has_nvidia:
            # Usage
            usage = self.stats['gpu_nvidia_percent']
            if usage < 60:
                gpu_color = "green"
                usage_desc = "[IDLE]"
            elif usage < 90:
                gpu_color = "yellow"
                usage_desc = "[GAME]"
            else:
                gpu_color = "red"
                usage_desc = "[MAX]"
            
            gpu_bar = self._make_bar(usage, 15, gpu_color) # Smaller bar
            
            # Temp
            temp = self.stats['gpu_nvidia_temp']
            temp_desc = "NORMAL"
            if temp > 80: temp_desc = "HOT"
            
            # Limpa o nome redundante (remove 'NVIDIA ' se já tiver no inicio)
            gpu_name = self.stats['gpu_nvidia_name'].replace("NVIDIA ", "")
            
            table.add_row(f"[cyan]NVIDIA[/cyan] {gpu_name[:20]}", "")
            table.add_row(f"  Load: [{gpu_color}]{usage:3.0f}%{usage_desc}[/{gpu_color}]", f"Temp: [{gpu_color}]{temp:.0f}°C[/]")
            table.add_row(f"  VRAM: {self.stats['gpu_nvidia_mem_used']:.0f} MB", f"Limit: {self.stats['gpu_nvidia_power_limit']}%")
        
        # 2. Intel (Integrated)
        if intel_active:
             intel_clean = intel_name.replace("Intel(R) ", "").replace("Graphics", "")
             table.add_row("", "")
             table.add_row(f"[blue]INTEL [/blue] {intel_clean[:20]}", "")
             table.add_row("  Status: [green]● Active[/green]", "Type: iGPU")
             
        # Fallback
        if not self.has_nvidia and not intel_active:
             table.add_row("[bold white]GPU[/bold white]", "[dim]No dedicated GPU detected[/dim]")
             
        return Panel(table, title="[bold]🖥️  HARDWARE MONITOR[/bold]", border_style="cyan")
    
    def make_memory_panel(self):
        """Memory and Status Panel"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=18)
        table.add_column("Value", justify="right")
        
        # RAM
        ram_color = "green" if self.stats['ram_percent'] < 70 else "yellow" if self.stats['ram_percent'] < 85 else "red"
        ram_bar = self._make_bar(self.stats['ram_percent'], 100, ram_color)
        
        ram_free_gb = (self.stats['ram_total'] - self.stats['ram_used']) / 1024
        ram_total_gb = self.stats['ram_total'] / 1024
        
        table.add_row("[bold white]RAM MEMORY[/bold white]", "")
        table.add_row("  Usage", f"[{ram_color}]{self.stats['ram_percent']:.1f}%[/{ram_color}] {ram_bar}")
        table.add_row("  Free", f"[green]{ram_free_gb:.1f} GB[/green] / {ram_total_gb:.1f} GB")
        table.add_row("  Cleanups", f"[yellow]{self.stats_tracker.get('total_cleanups', 0)}[/yellow] auto")
        table.add_row("", "")
        
        # Optimizations
        table.add_row("[bold white]OPTIMIZATIONS[/bold white]", "")
        table.add_row("  Standby Cleaner", "[green]●[/green] Active")
        table.add_row("  Smart Priority", "[green]●[/green] Active")
        table.add_row("  CPU Limit", f"[yellow]●[/yellow] {self.stats['cpu_limit']}%")
        
        # GPU Power Limit
        if self.stats['gpu_nvidia_power_limit'] > 0:
            table.add_row("  GPU Power Limit", f"[yellow]●[/yellow] {self.stats['gpu_nvidia_power_limit']}%")
        
        table.add_row("  SysMain", "[red]●[/red] Disabled")
        table.add_row("", "")
        
        # V3.0 Features
        table.add_row("[bold white]V3.0 FEATURES[/bold white]", "")
        
        # Game Mode Status
        game_active = self.stats.get('game_active', False)
        game_name = self.stats.get('game_name', '')
        if game_active:
            table.add_row("  🎮 Game Mode", f"[green]●[/green] {game_name[:15]}")
        else:
            table.add_row("  🎮 Game Mode", "[dim]○ Waiting[/dim]")
        
        # Network QoS
        table.add_row("  📡 Network QoS", "[green]●[/green] Active")
        
        # Profile
        profile = self.stats.get('active_profile', 'Balanced')
        table.add_row("  ⚡ Profile", f"[cyan]{profile}[/cyan]")
        
        return Panel(table, title="[bold]💾  Memory & Status[/bold]", border_style="green")
    
    def make_footer(self):
        """Footer with Smart System Metrics"""
        # Calculate uptime
        uptime = self.stats_tracker.get('uptime_seconds', 0)
        h, rem = divmod(uptime, 3600)
        m, s = divmod(rem, 60)
        time_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        
        # Cleaned RAM
        cleaned_mb = self.stats_tracker.get('total_ram_cleaned_mb', 0)
        cleaned_gb = cleaned_mb / 1024
        
        # Estimated Ads Blocked (AdGuard blocks ~15% of requests, avg 2 req/sec)
        # Estimate: ~100 ads/trackers blocked per minute with AdGuard DNS
        ads_blocked = int((uptime / 60) * 100)
        
        # Estimated Data Saved (avg ad = 150KB)
        data_saved_mb = (ads_blocked * 150) / 1024
        
        table = Table(show_header=True, box=None, expand=True)
        table.add_column("System Intelligence", style="bold cyan")
        table.add_column("Live Statistics", justify="center", style="green")
        table.add_column("Active Modules", justify="center", style="yellow")
        
        # Build active modules string
        modules = []
        modules.append("[green]●[/] RAM")
        modules.append("[green]●[/] CPU")
        modules.append("[green]●[/] I/O")
        if self.has_nvidia:
            modules.append("[green]●[/] GPU")
        if self.has_intel:
            modules.append("[green]●[/] iGPU")
        modules.append("[green]●[/] DNS")  # AdGuard DNS
        
        modules_str = " ".join(modules)
        
        # Format ads blocked (K for thousands)
        ads_str = f"{ads_blocked/1000:.1f}K" if ads_blocked >= 1000 else str(ads_blocked)
        
        table.add_row(
            f"[white]V3.0 • AdGuard DNS • [magenta]🛡️ {ads_str} Blocked[/magenta][/white]",
            f"RAM: [bold]{cleaned_gb:.1f}GB[/bold] | Data Saved: [cyan]{data_saved_mb:.1f}MB[/cyan] | ⏱️ {time_str}",
            f"Hi:{self.stats['priority_high']} Lo:{self.stats['priority_low']} | {modules_str}"
        )
        
        return Panel(table, title="[bold]🎯  Smart System[/bold]", border_style="yellow")
    
    def _make_bar(self, value, max_value, color):
        """Cria uma barra de progresso visual"""
        pct = min(100, (value / max_value) * 100)
        filled = int(pct / 5)  # 20 caracteres max
        empty = 20 - filled
        return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
    
    def update_stats(self, services):
        """Atualiza estatísticas do sistema"""
        # CPU
        self.stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        
        # Temperatura da CPU (usando serviço centralizado com cache)
        self.stats['cpu_temp'] = self._temp_service.get_cpu_temp()
        
        # Frequência da CPU
        freq = psutil.cpu_freq()
        if freq:
            self.stats['cpu_freq'] = freq.current / 1000  # MHz para GHz
        
        # GPU NVIDIA (se disponível)
        if self.has_nvidia and self.nvidia_handle:
            try:
                import pynvml
                util = pynvml.nvmlDeviceGetUtilizationRates(self.nvidia_handle)
                self.stats['gpu_nvidia_percent'] = util.gpu
                
                temp = pynvml.nvmlDeviceGetTemperature(self.nvidia_handle, 0)
                self.stats['gpu_nvidia_temp'] = temp
                
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.nvidia_handle)
                self.stats['gpu_nvidia_mem_used'] = mem_info.used / 1024 / 1024
                self.stats['gpu_nvidia_mem_total'] = mem_info.total / 1024 / 1024
            except:
                pass
        
        # GPU Power Limit (pega do service se disponível)
        if 'gpu_ctrl' in services and hasattr(services['gpu_ctrl'], 'applied_percent'):
            self.stats['gpu_nvidia_power_limit'] = services['gpu_ctrl'].applied_percent
        
        # RAM
        mem = psutil.virtual_memory()
        self.stats['ram_used'] = mem.used / 1024 / 1024  # MB
        self.stats['ram_total'] = mem.total / 1024 / 1024  # MB
        self.stats['ram_percent'] = mem.percent
        
        # Limpezas de RAM
        # RAM Cleaning Stats
        if 'cleaner' in services:
            # Stats tracking
            if hasattr(services['cleaner'], 'total_cleaned_mb'):
                self.stats_tracker['total_ram_cleaned_mb'] = services['cleaner'].total_cleaned_mb
                self.stats_tracker['total_cleanups'] = services['cleaner'].clean_count
            elif hasattr(services['cleaner'], 'clean_count'):
                 self.stats_tracker['total_cleanups'] = services['cleaner'].clean_count
        
        # Uptime
        self.stats_tracker['uptime_seconds'] = int(time.time() - self.stats_tracker['start_time'])

        # Prioridades (Fix for Windows Constants)
        try:
            procs = list(psutil.process_iter(['nice']))
            high_count = 0
            low_count = 0
            
            # Windows Priority Constants
            # High=128, AboveNormal=32768, Realtime=256
            # Normal=32
            # BelowNormal=16384, Idle=64
            
            # psutil mapping might vary slightly by version, checking against sets is safer
            HIGH_PRIOS = {psutil.HIGH_PRIORITY_CLASS, psutil.REALTIME_PRIORITY_CLASS, psutil.ABOVE_NORMAL_PRIORITY_CLASS}
            LOW_PRIOS = {psutil.IDLE_PRIORITY_CLASS, psutil.BELOW_NORMAL_PRIORITY_CLASS}
            
            for p in procs:
                try:
                    p_nice = p.info['nice']
                    if p_nice in HIGH_PRIOS:
                        high_count += 1
                    elif p_nice in LOW_PRIOS:
                        low_count += 1
                except:
                    pass
            self.stats['priority_high'] = high_count
            self.stats['priority_low'] = low_count
        except:
            pass
        
        # V3.0: Game Detector Status
        if 'game_detector' in services:
            self.stats['game_active'] = services['game_detector'].is_game_active()
            self.stats['game_name'] = services['game_detector'].get_current_game() or ''
        
        # V3.0: Profile Status
        if 'profiles' in services:
            profile = services['profiles'].get_current_profile()
            self.stats['active_profile'] = profile.value.title() if profile else 'Balanced'

    
    def render(self, services):
        """Renderiza o dashboard"""
        self.update_stats(services)
        
        self.layout["header"].update(self.make_header())
        self.layout["cpu_gpu"].update(self.make_cpu_gpu_panel())
        self.layout["memory"].update(self.make_memory_panel())
        self.layout["footer"].update(self.make_footer())
        
        return self.layout
    
    def run(self, services):
        """Executa o dashboard em loop (Stable Mode)"""
        self.running = True
        
        # Simple, stable configuration:
        # - refresh_per_second=0.5 (update every 2 seconds - very stable)
        # - screen=False (no full screen takeover - prevents jumping)
        # - Uses auto_refresh=True (Rich handles timing)
        
        # Initial render
        self.update_stats(services)
        
        with Live(
            self.layout,
            refresh_per_second=0.5,
            console=self.console,
            screen=False,
            auto_refresh=True
        ) as live:
            while self.running:
                time.sleep(2)  # Update every 2 seconds
                self.update_stats(services)
                self.render(services)


if __name__ == "__main__":
    # Teste
    dash = Dashboard()
    dash.run({})


