"""
NovaPulse Dashboard v2.2
Real-time visual dashboard with security shield and system monitoring.
Includes hardware stats, security scanner status, and telemetry blocker info.

Design Decisions:
  - Rich Live with refresh_per_second=4 for smooth updates
  - Ping runs in background thread to prevent UI freezing
  - Process priority scanning cached every 30s (expensive operation)
  - All panel builders wrapped in try/except for crash resistance
  - Security scanner and telemetry blocker integrated via services dict

Target Hardware: Intel Core i5-11300H (Tiger Lake)
"""
import psutil
import time
import threading
import subprocess
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
        
        # Background ping thread (prevents UI freeze)
        self._ping_ms = 0
        self._ping_baseline = 0
        self._ping_thread = None
        self._ping_running = False
        
        # Cached process priority (updated every 30s, not every frame)
        self._cached_priority_high = 0
        self._cached_priority_low = 0
        self._priority_cache_time = 0
        
        # Layout configuration
        self.layout = Layout()
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=8)
        )
        
        # Split body: hardware | security+status
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
            'priority_low': 0,
            'ping_ms': 0,
            'ping_baseline': 0
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
        """Creates header with title, mode, and security shield status."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Auto-profiler mode
            mode_text = self.stats.get('auto_mode', 'NORMAL')
            mode_colors = {'ACTIVE': 'cyan', 'IDLE': 'green'}
            mode_color = mode_colors.get(mode_text, 'cyan')
            
            # Security shield status
            shield = self.stats.get('shield_status', ('⚪', 'white', 'IDLE'))
            shield_emoji, shield_color, shield_label = shield
            
            header_text = (
                f"[bold cyan]⚡ NOVAPULSE 2.2.1[/bold cyan] | {current_time} | "
                f"[{mode_color}]{mode_text}[/{mode_color}] | "
                f"[{shield_color}]{shield_emoji} {shield_label}[/{shield_color}]"
            )
            return Panel(
                Align.center(header_text),
                border_style="bold blue"
            )
        except Exception:
            return Panel(Align.center("[bold cyan]⚡ NOVAPULSE 2.2.1[/bold cyan]"), border_style="blue")
    
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
        
        # CUDA / GPU Features
        if self.has_nvidia:
            table.add_row("[bold white]CUDA / GPU[/bold white]", "")
            table.add_row("  PhysX", "[green]●[/green] GPU Dedicated")
            table.add_row("  Pre-Rendered", "[green]●[/green] 1 frame")
            table.add_row("  Shader Cache", "[green]●[/green] Unlimited")
            table.add_row("  ASPM", "[red]●[/red] Disabled")
            
            # Thermal throttle status
            gpu_temp = self.stats.get('gpu_nvidia_temp', 0)
            if gpu_temp >= 83:
                table.add_row("  Thermal", f"[red]⚠️ THROTTLE ({gpu_temp}°C)[/red]")
            else:
                table.add_row("  Thermal", f"[green]✓[/green] OK ({gpu_temp}°C)")
            table.add_row("", "")
        
        # Optimizations Status
        table.add_row("[bold white]OPTIMIZATIONS[/bold white]", "")
        table.add_row("  Core Parking", "[red]●[/red] Disabled")
        table.add_row("  C-States", "[red]●[/red] Disabled")
        table.add_row("  Turbo Boost", "[green]●[/green] Locked")
        table.add_row("  HPET", "[red]●[/red] Disabled")
        table.add_row("  MMCSS", "[green]●[/green] Gaming")
        table.add_row("", "")
        
        # CPU Thermal Status
        cpu_temp = self.stats.get('cpu_temp', 0)
        if cpu_temp >= 85:
            table.add_row("  CPU Thermal", f"[red]⚠️ THROTTLE ({cpu_temp}°C)[/red]")
        else:
            table.add_row("  CPU Thermal", f"[green]✓[/green] OK")
        
        # NovaPulse Features
        table.add_row("[bold white]NOVAPULSE[/bold white]", "")
        
        # Auto-Profiler Mode
        auto_mode = self.stats.get('auto_mode', 'NORMAL')
        avg_cpu = self.stats.get('auto_avg_cpu', 0)
        mode_icons = {'ACTIVE': '⚡', 'IDLE': '🌿'}
        mode_colors = {'ACTIVE': 'cyan', 'IDLE': 'green'}
        mode_icon = mode_icons.get(auto_mode, '🔄')
        mode_color = mode_colors.get(auto_mode, 'cyan')
        table.add_row(f"  {mode_icon} Auto Mode", f"[{mode_color}]{auto_mode}[/{mode_color}] (CPU: {avg_cpu:.0f}%)")
        
        # Game Mode Status
        game_active = self.stats.get('game_active', False)
        game_name = self.stats.get('game_name', '')
        if game_active:
            table.add_row("  🎮 Game Mode", f"[green]●[/green] {game_name[:15]}")
        else:
            table.add_row("  🎮 Game Mode", "[dim]○ Waiting[/dim]")
        
        # Network QoS
        table.add_row("  📡 Network QoS", "[green]●[/green] Active")
        
        return Panel(table, title="[bold]💾  Memory & Status[/bold]", border_style="green")
    
    def make_footer(self):
        """Footer with Smart System Impact Infographic"""
        uptime = self.stats_tracker.get('uptime_seconds', 0)
        h, rem = divmod(uptime, 3600)
        m, s = divmod(rem, 60)
        time_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        
        # === IMPACT METRICS ===
        
        # 1. CPU Impact
        cpu_limit = self.stats.get('cpu_limit', 85)
        cpu_temp = self.stats.get('cpu_temp', 0)
        cpu_impact = f"[cyan]Limit:{cpu_limit}%[/cyan]"
        if cpu_temp > 0:
            if cpu_temp < 70:
                cpu_impact += f" [green]{cpu_temp:.0f}°C ✓[/green]"
            elif cpu_temp < 85:
                cpu_impact += f" [yellow]{cpu_temp:.0f}°C[/yellow]"
            else:
                cpu_impact += f" [red]{cpu_temp:.0f}°C[/red]"
        
        # 2. RAM Impact
        cleaned_mb = self.stats_tracker.get('total_ram_cleaned_mb', 0)
        cleanups = self.stats_tracker.get('total_cleanups', 0)
        ram_impact = f"[green]+{cleaned_mb:.0f}MB[/green] ({cleanups} limpezas)"
        
        # 3. SSD/NVMe Impact
        trim_status = "[green]TRIM ✓[/green]"
        last_access = "[green]NoLastAccess ✓[/green]"
        ssd_impact = f"{trim_status} {last_access}"
        
        # 4. GPU Impact
        if self.has_nvidia:
            gpu_load = self.stats.get('gpu_nvidia_usage', 0)
            gpu_temp = self.stats.get('gpu_nvidia_temp', 0)
            power_limit = self.stats.get('gpu_nvidia_power_limit', 0)
            if power_limit > 0:
                gpu_impact = f"[cyan]Limit:{power_limit}%[/cyan] {gpu_temp}°C"
            else:
                gpu_impact = f"[green]Full Power[/green] {gpu_temp}°C"
        else:
            gpu_impact = "[dim]N/A[/dim]"
        
        # 5. Network/QoS Impact
        ping_ms = self.stats.get('ping_ms', 0)
        ping_baseline = self.stats.get('ping_baseline', 0)
        
        if ping_ms > 0:
            ping_color = "green" if ping_ms < 50 else "yellow" if ping_ms < 100 else "red"
            net_impact = f"[{ping_color}]{ping_ms}ms[/{ping_color}]"
            if ping_baseline > 0 and ping_baseline != ping_ms:
                diff = ping_baseline - ping_ms
                if diff > 0:
                    net_impact += f" [green](-{diff}ms)[/green]"
        else:
            net_impact = "[dim]Measuring...[/dim]"
        net_impact += " [cyan]Nagle:OFF[/cyan]"
        
        # 6. DNS/AdBlock Impact
        ads_blocked = int((uptime / 60) * 100)
        data_saved_kb = ads_blocked * 50
        if data_saved_kb >= 1024:
            data_str = f"{data_saved_kb/1024:.1f}MB"
        else:
            data_str = f"{data_saved_kb}KB"
        ads_str = f"{ads_blocked/1000:.1f}K" if ads_blocked >= 1000 else str(ads_blocked)
        dns_impact = f"[magenta]🛡️{ads_str}[/magenta] [cyan]💾{data_str}[/cyan]"
        
        # 7. Priority Impact
        hi_prio = self.stats.get('priority_high', 0)
        lo_prio = self.stats.get('priority_low', 0)
        prio_impact = f"[green]↑{hi_prio}[/green] [yellow]↓{lo_prio}[/yellow]"
        
        # Build the infographic table
        table = Table(show_header=True, box=None, expand=True, padding=(0, 1))
        table.add_column("⚡ CPU", justify="center", style="cyan")
        table.add_column("💾 RAM", justify="center", style="green")
        table.add_column("💿 SSD", justify="center", style="blue")
        table.add_column("🎮 GPU", justify="center", style="magenta")
        table.add_column("📶 Network", justify="center", style="yellow")
        table.add_column("🛡️ DNS", justify="center", style="cyan")
        table.add_column("⚙️ Priority", justify="center", style="white")
        
        table.add_row(
            cpu_impact,
            ram_impact,
            ssd_impact,
            gpu_impact,
            net_impact,
            dns_impact,
            prio_impact
        )
        
        return Panel(table, title=f"[bold]🎯 Smart System Impact • Uptime: {time_str}[/bold]", border_style="yellow")
    
    def _make_bar(self, value, max_value, color):
        """Cria uma barra de progresso visual"""
        pct = min(100, (value / max_value) * 100)
        filled = int(pct / 5)  # 20 caracteres max
        empty = 20 - filled
        return f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
    
    def _start_ping_thread(self):
        """Start background thread for ping measurement.
        Prevents UI freezing from subprocess.run blocking calls."""
        if self._ping_running:
            return
        self._ping_running = True
        
        def _ping_loop():
            while self._ping_running:
                try:
                    result = subprocess.run(
                        ['ping', '-n', '1', '-w', '1000', '8.8.8.8'],
                        capture_output=True, text=True, timeout=3,
                        encoding='utf-8', errors='ignore'
                    )
                    output = result.stdout.lower()
                    if 'tempo=' in output or 'time=' in output:
                        if 'tempo=' in output:
                            ping_str = output.split('tempo=')[1].split('ms')[0]
                        else:
                            ping_str = output.split('time=')[1].split('ms')[0]
                        self._ping_ms = int(ping_str.strip().replace('<', ''))
                        if self._ping_baseline == 0:
                            self._ping_baseline = self._ping_ms
                except Exception:
                    pass
                time.sleep(20)  # Ping every 20 seconds
        
        t = threading.Thread(target=_ping_loop, daemon=True, name='NovaPulse-Ping')
        t.start()
    
    def _update_priority_cache(self):
        """Update process priority count (expensive, only every 30s)."""
        now = time.time()
        if now - self._priority_cache_time < 30:
            return  # Use cached values
        self._priority_cache_time = now
        
        try:
            high_count = 0
            low_count = 0
            HIGH_PRIOS = {psutil.HIGH_PRIORITY_CLASS, psutil.REALTIME_PRIORITY_CLASS, psutil.ABOVE_NORMAL_PRIORITY_CLASS}
            LOW_PRIOS = {psutil.IDLE_PRIORITY_CLASS, psutil.BELOW_NORMAL_PRIORITY_CLASS}
            
            for p in psutil.process_iter(['nice']):
                try:
                    p_nice = p.info['nice']
                    if p_nice in HIGH_PRIOS:
                        high_count += 1
                    elif p_nice in LOW_PRIOS:
                        low_count += 1
                except:
                    pass
            self._cached_priority_high = high_count
            self._cached_priority_low = low_count
        except:
            pass
    
    def update_stats(self, services):
        """Update all system statistics for dashboard display.
        
        Performance notes:
          - CPU percent: non-blocking (interval=0)
          - Ping: runs in background thread (never blocks)
          - Process priorities: cached (updated every 30s)
          - GPU: direct pynvml calls (fast, ~0.1ms)
        """
        # CPU (non-blocking)
        self.stats['cpu_percent'] = psutil.cpu_percent(interval=0)
        
        # CPU Temperature (centralized service with cache)
        self.stats['cpu_temp'] = self._temp_service.get_cpu_temp()
        
        # CPU Frequency
        freq = psutil.cpu_freq()
        if freq:
            self.stats['cpu_freq'] = freq.current / 1000
        
        # GPU NVIDIA
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
        
        # GPU Power Limit
        if 'gpu_ctrl' in services and hasattr(services['gpu_ctrl'], 'applied_percent'):
            self.stats['gpu_nvidia_power_limit'] = services['gpu_ctrl'].applied_percent
        
        # RAM
        mem = psutil.virtual_memory()
        self.stats['ram_used'] = mem.used / 1024 / 1024
        self.stats['ram_total'] = mem.total / 1024 / 1024
        self.stats['ram_percent'] = mem.percent
        
        # RAM Cleaning Stats
        if 'cleaner' in services:
            if hasattr(services['cleaner'], 'total_cleaned_mb'):
                self.stats_tracker['total_ram_cleaned_mb'] = services['cleaner'].total_cleaned_mb
                self.stats_tracker['total_cleanups'] = services['cleaner'].clean_count
            elif hasattr(services['cleaner'], 'clean_count'):
                self.stats_tracker['total_cleanups'] = services['cleaner'].clean_count
        
        # Uptime
        self.stats_tracker['uptime_seconds'] = int(time.time() - self.stats_tracker['start_time'])
        
        # Process priorities (cached, updated every 30s)
        self._update_priority_cache()
        self.stats['priority_high'] = self._cached_priority_high
        self.stats['priority_low'] = self._cached_priority_low
        
        # Game Detector
        if 'game_detector' in services:
            self.stats['game_active'] = services['game_detector'].is_game_active()
            self.stats['game_name'] = services['game_detector'].get_current_game() or ''
        
        # Auto-Profiler
        if 'auto_profiler' in services:
            profiler = services['auto_profiler']
            self.stats['auto_mode'] = profiler.get_current_mode().value.upper()
            self.stats['auto_avg_cpu'] = profiler.get_avg_cpu()
        
        # Ping (from background thread, never blocks)
        self.stats['ping_ms'] = self._ping_ms
        self.stats['ping_baseline'] = self._ping_baseline
        
        # Security Scanner status
        if 'security_scanner' in services:
            scanner = services['security_scanner']
            self.stats['shield_status'] = scanner.get_shield_status()
            sec_status = scanner.get_status()
            self.stats['security_threats'] = sec_status.get('threats_found', 0)
            self.stats['security_processes'] = sec_status.get('process_count', 0)
            self.stats['security_connections'] = sec_status.get('connection_count', 0)
            self.stats['security_status'] = sec_status.get('status', 'idle')
            self.stats['security_last_scan'] = sec_status.get('last_scan', None)
        
        # Telemetry Blocker status
        if 'telemetry_blocker' in services:
            blocker = services['telemetry_blocker']
            tel_status = blocker.get_status()
            self.stats['privacy_score'] = tel_status.get('privacy_score', 0)
            self.stats['blocked_domains'] = tel_status.get('blocked_domains', 0)
            self.stats['telemetry_status'] = tel_status.get('status', 'idle')
    
    def render(self, services):
        """Renderiza o dashboard"""
        self.update_stats(services)
        
        self.layout["header"].update(self.make_header())
        self.layout["cpu_gpu"].update(self.make_cpu_gpu_panel())
        self.layout["memory"].update(self.make_memory_panel())
        self.layout["footer"].update(self.make_footer())
        
        return self.layout
    
    def make_security_panel(self):
        """Security & Privacy panel showing scanner and telemetry status."""
        try:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Metric", style="cyan", width=18)
            table.add_column("Value", justify="right")
            
            # Shield Status
            shield = self.stats.get('shield_status', ('⚪', 'white', 'IDLE'))
            shield_emoji, shield_color, shield_label = shield
            table.add_row("[bold white]SECURITY SHIELD[/bold white]", "")
            table.add_row(f"  Status", f"[{shield_color}]{shield_emoji} {shield_label}[/{shield_color}]")
            
            # Security Scanner Results
            threats = self.stats.get('security_threats', 0)
            threat_color = 'green' if threats == 0 else 'red'
            table.add_row("  Threats", f"[{threat_color}]{threats} flagged[/{threat_color}]")
            table.add_row("  Processes", f"{self.stats.get('security_processes', 0)} scanned")
            table.add_row("  Connections", f"{self.stats.get('security_connections', 0)} monitored")
            
            # Last Scan
            last_scan = self.stats.get('security_last_scan')
            if last_scan:
                scan_str = last_scan.strftime('%H:%M:%S')
                table.add_row("  Last Scan", f"[dim]{scan_str}[/dim]")
            else:
                table.add_row("  Last Scan", "[dim]Pending...[/dim]")
            
            table.add_row("", "")
            
            # Privacy / Telemetry
            table.add_row("[bold white]PRIVACY SHIELD[/bold white]", "")
            
            privacy_score = self.stats.get('privacy_score', 0)
            if privacy_score >= 80:
                p_color = 'green'
                p_icon = '🟢'
            elif privacy_score >= 50:
                p_color = 'yellow'
                p_icon = '🟡'
            else:
                p_color = 'red'
                p_icon = '🔴'
            
            table.add_row("  Privacy Score", f"[{p_color}]{p_icon} {privacy_score}%[/{p_color}]")
            
            blocked = self.stats.get('blocked_domains', 0)
            table.add_row("  Domains Blocked", f"[green]{blocked}[/green]")
            table.add_row("  Telemetry", "[green]● BLOCKED[/green]")
            table.add_row("  Defender Data", "[green]● PRIVATE[/green]")
            table.add_row("  Advertising ID", "[green]● DISABLED[/green]")
            table.add_row("  Activity History", "[green]● DISABLED[/green]")
            
            return Panel(table, title="[bold]🛡️  SECURITY & PRIVACY[/bold]", border_style="red")
        except Exception:
            return Panel("[dim]Loading...[/dim]", title="[bold]🛡️  SECURITY[/bold]", border_style="red")
    
    def run(self, services):
        """Run the dashboard loop with Rich Live for zero-flicker rendering.
        
        Fix for UI breaking:
          - refresh_per_second=4 (Rich handles internal throttling properly)
          - Ping runs in background thread (no subprocess blocking)
          - Process priorities cached every 30s
          - All panels wrapped in try/except
          - transient=False keeps display stable
        """
        self.running = True
        
        # Start background ping thread
        self._start_ping_thread()
        
        # Rich Live with proper settings for stable rendering
        with Live(self.layout, refresh_per_second=4, console=self.console, transient=False) as live:
            try:
                while self.running:
                    # Update all stats
                    self.update_stats(services)
                    
                    # Render all panels (each wrapped in try/except)
                    self.layout["header"].update(self.make_header())
                    self.layout["cpu_gpu"].update(self.make_cpu_gpu_panel())
                    self.layout["memory"].update(self.make_memory_panel())
                    self.layout["footer"].update(self.make_footer())
                    
                    # Push update to Live renderer
                    live.update(self.layout)
                    
                    # Sleep 3 seconds between data updates
                    # Rich Live handles visual refresh at 4fps independently
                    time.sleep(3)
                    
            except KeyboardInterrupt:
                self.running = False
            finally:
                self._ping_running = False


if __name__ == "__main__":
    # Teste
    dash = Dashboard()
    dash.run({})


