"""
NovaPulse - Dashboard Server
Servidor HTTP local para dashboard HTML sem flickering
"""
import threading
import json
import time
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

try:
    import pynvml
    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
except:
    NVIDIA_AVAILABLE = False


class DashboardData:
    """Dados compartilhados do dashboard"""
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.gpu_handle = None
        
        if NVIDIA_AVAILABLE:
            try:
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            except:
                pass
    
    def update(self, services=None):
        """Atualiza dados do sistema"""
        with self.lock:
            # CPU
            self.data['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            self.data['cpu_cores'] = psutil.cpu_percent(percpu=True)
            
            freq = psutil.cpu_freq()
            self.data['cpu_freq'] = freq.current if freq else 0
            
            # RAM
            mem = psutil.virtual_memory()
            self.data['ram_percent'] = mem.percent
            self.data['ram_used_gb'] = mem.used / (1024**3)
            self.data['ram_total_gb'] = mem.total / (1024**3)
            
            # GPU NVIDIA
            if NVIDIA_AVAILABLE and self.gpu_handle:
                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                    self.data['gpu_percent'] = util.gpu
                    self.data['gpu_temp'] = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, 0)
                    
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                    self.data['gpu_vram_used'] = mem_info.used / (1024**3)
                    self.data['gpu_vram_total'] = mem_info.total / (1024**3)
                    
                    name = pynvml.nvmlDeviceGetName(self.gpu_handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')
                    self.data['gpu_name'] = name
                except:
                    pass
            
            # Auto-Profiler
            if services and 'auto_profiler' in services:
                profiler = services['auto_profiler']
                self.data['mode'] = profiler.get_current_mode().value.upper()
                self.data['cpu_limit'] = profiler.thermal_throttle_percent if hasattr(profiler, 'thermal_throttle_percent') else 85
            else:
                self.data['mode'] = 'NORMAL'
                self.data['cpu_limit'] = 85
            
            self.data['timestamp'] = time.strftime('%H:%M:%S')
    
    def get_json(self):
        with self.lock:
            return json.dumps(self.data)


# Singleton
_dashboard_data = DashboardData()


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="2">
    <title>NovaPulse Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 15px;
            background: rgba(0,200,255,0.1);
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid rgba(0,200,255,0.3);
        }
        .header h1 { color: #00d4ff; font-size: 28px; }
        .header .mode {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 20px;
        }
        .mode-BOOST { background: #ff4444; }
        .mode-NORMAL { background: #00aaff; }
        .mode-ECO { background: #44ff44; color: #000; }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        
        .panel {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .panel h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 1px solid rgba(0,200,255,0.3);
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .metric-label { color: #888; }
        .metric-value { font-weight: bold; font-family: 'Consolas', monospace; }
        
        .bar-container {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 5px;
        }
        .bar {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .bar-green { background: linear-gradient(90deg, #00ff88, #00cc66); }
        .bar-yellow { background: linear-gradient(90deg, #ffcc00, #ff9900); }
        .bar-red { background: linear-gradient(90deg, #ff4444, #cc0000); }
        
        .cores-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .core {
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .core-label { font-size: 12px; color: #666; }
        .core-value { font-size: 18px; font-weight: bold; }
        
        .status-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-on { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .status-off { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
        
        .footer {
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ NOVAPULSE 2.0</h1>
        <span class="mode mode-{{MODE}}">{{MODE}}</span>
        <span style="margin-left: 20px; color: #888;">{{TIME}}</span>
    </div>
    
    <div class="grid">
        <div class="panel">
            <h2>🖥️ CPU & Cores</h2>
            <div class="metric">
                <span class="metric-label">Total Usage</span>
                <span class="metric-value" style="color: {{CPU_COLOR}}">{{CPU_PERCENT}}%</span>
            </div>
            <div class="bar-container">
                <div class="bar {{CPU_BAR_CLASS}}" style="width: {{CPU_PERCENT}}%"></div>
            </div>
            <div class="metric">
                <span class="metric-label">Frequency</span>
                <span class="metric-value">{{CPU_FREQ}} MHz</span>
            </div>
            <div class="metric">
                <span class="metric-label">Limit</span>
                <span class="metric-value" style="color: #ffcc00">{{CPU_LIMIT}}%</span>
            </div>
            
            <div class="cores-grid">
                {{CORES_HTML}}
            </div>
        </div>
        
        <div class="panel">
            <h2>🎮 GPU NVIDIA</h2>
            <div class="metric">
                <span class="metric-label">{{GPU_NAME}}</span>
                <span class="metric-value"></span>
            </div>
            <div class="metric">
                <span class="metric-label">GPU Load</span>
                <span class="metric-value" style="color: {{GPU_COLOR}}">{{GPU_PERCENT}}%</span>
            </div>
            <div class="bar-container">
                <div class="bar {{GPU_BAR_CLASS}}" style="width: {{GPU_PERCENT}}%"></div>
            </div>
            <div class="metric">
                <span class="metric-label">Temperature</span>
                <span class="metric-value" style="color: {{GPU_TEMP_COLOR}}">{{GPU_TEMP}}°C</span>
            </div>
            <div class="metric">
                <span class="metric-label">VRAM</span>
                <span class="metric-value">{{GPU_VRAM_USED:.1f}} / {{GPU_VRAM_TOTAL:.1f}} GB</span>
            </div>
        </div>
        
        <div class="panel">
            <h2>💾 Memory</h2>
            <div class="metric">
                <span class="metric-label">RAM Usage</span>
                <span class="metric-value" style="color: {{RAM_COLOR}}">{{RAM_PERCENT}}%</span>
            </div>
            <div class="bar-container">
                <div class="bar {{RAM_BAR_CLASS}}" style="width: {{RAM_PERCENT}}%"></div>
            </div>
            <div class="metric">
                <span class="metric-label">Used / Total</span>
                <span class="metric-value">{{RAM_USED:.1f}} / {{RAM_TOTAL:.1f}} GB</span>
            </div>
        </div>
        
        <div class="panel">
            <h2>⚙️ Optimizations Active</h2>
            <div class="status-item"><div class="status-dot status-on"></div>Core Parking OFF</div>
            <div class="status-item"><div class="status-dot status-on"></div>C-States Disabled</div>
            <div class="status-item"><div class="status-dot status-on"></div>Turbo Boost Locked</div>
            <div class="status-item"><div class="status-dot status-on"></div>HPET Disabled</div>
            <div class="status-item"><div class="status-dot status-on"></div>MMCSS Gaming</div>
            <div class="status-item"><div class="status-dot status-on"></div>CUDA Optimized</div>
            <div class="status-item"><div class="status-dot status-on"></div>Pre-Rendered Frames: 1</div>
            <div class="status-item"><div class="status-dot status-on"></div>Shader Cache: Unlimited</div>
        </div>
    </div>
    
    <div class="footer">
        NovaPulse 2.0 | Thermal Protection: CPU 85°C | GPU 83°C | Auto-refresh: 2s
    </div>
</body>
</html>
'''


class DashboardHandler(BaseHTTPRequestHandler):
    """Handler HTTP para o dashboard"""
    
    def log_message(self, format, *args):
        pass  # Silencia logs
    
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(_dashboard_data.get_json().encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Atualiza dados
            _dashboard_data.update()
            data = _dashboard_data.data
            
            # Gera HTML dos cores
            cores_html = ""
            for i, usage in enumerate(data.get('cpu_cores', [])):
                color = '#00ff88' if usage < 50 else '#ffcc00' if usage < 80 else '#ff4444'
                cores_html += f'<div class="core"><div class="core-label">C{i}</div><div class="core-value" style="color:{color}">{usage:.0f}%</div></div>'
            
            # Determina cores e classes
            cpu_pct = data.get('cpu_percent', 0)
            cpu_color = '#00ff88' if cpu_pct < 50 else '#ffcc00' if cpu_pct < 80 else '#ff4444'
            cpu_bar = 'bar-green' if cpu_pct < 50 else 'bar-yellow' if cpu_pct < 80 else 'bar-red'
            
            gpu_pct = data.get('gpu_percent', 0)
            gpu_color = '#00ff88' if gpu_pct < 60 else '#ffcc00' if gpu_pct < 90 else '#ff4444'
            gpu_bar = 'bar-green' if gpu_pct < 60 else 'bar-yellow' if gpu_pct < 90 else 'bar-red'
            
            gpu_temp = data.get('gpu_temp', 0)
            gpu_temp_color = '#00ff88' if gpu_temp < 70 else '#ffcc00' if gpu_temp < 83 else '#ff4444'
            
            ram_pct = data.get('ram_percent', 0)
            ram_color = '#00ff88' if ram_pct < 70 else '#ffcc00' if ram_pct < 85 else '#ff4444'
            ram_bar = 'bar-green' if ram_pct < 70 else 'bar-yellow' if ram_pct < 85 else 'bar-red'
            
            # Substitui placeholders
            html = HTML_TEMPLATE
            html = html.replace('{{MODE}}', data.get('mode', 'NORMAL'))
            html = html.replace('{{TIME}}', data.get('timestamp', '--:--:--'))
            html = html.replace('{{CPU_PERCENT}}', f"{cpu_pct:.1f}")
            html = html.replace('{{CPU_COLOR}}', cpu_color)
            html = html.replace('{{CPU_BAR_CLASS}}', cpu_bar)
            html = html.replace('{{CPU_FREQ}}', f"{data.get('cpu_freq', 0):.0f}")
            html = html.replace('{{CPU_LIMIT}}', str(data.get('cpu_limit', 85)))
            html = html.replace('{{CORES_HTML}}', cores_html)
            html = html.replace('{{GPU_NAME}}', data.get('gpu_name', 'NVIDIA GPU'))
            html = html.replace('{{GPU_PERCENT}}', f"{gpu_pct:.0f}")
            html = html.replace('{{GPU_COLOR}}', gpu_color)
            html = html.replace('{{GPU_BAR_CLASS}}', gpu_bar)
            html = html.replace('{{GPU_TEMP}}', str(gpu_temp))
            html = html.replace('{{GPU_TEMP_COLOR}}', gpu_temp_color)
            html = html.replace('{{GPU_VRAM_USED:.1f}}', f"{data.get('gpu_vram_used', 0):.1f}")
            html = html.replace('{{GPU_VRAM_TOTAL:.1f}}', f"{data.get('gpu_vram_total', 0):.1f}")
            html = html.replace('{{RAM_PERCENT}}', f"{ram_pct:.1f}")
            html = html.replace('{{RAM_COLOR}}', ram_color)
            html = html.replace('{{RAM_BAR_CLASS}}', ram_bar)
            html = html.replace('{{RAM_USED:.1f}}', f"{data.get('ram_used_gb', 0):.1f}")
            html = html.replace('{{RAM_TOTAL:.1f}}', f"{data.get('ram_total_gb', 0):.1f}")
            
            self.wfile.write(html.encode())


class DashboardServer:
    """Servidor do dashboard"""
    
    def __init__(self, port=8888):
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Inicia o servidor em background"""
        self.server = HTTPServer(('127.0.0.1', self.port), DashboardHandler)
        self.running = True
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        print(f"[DASHBOARD] Servidor iniciado em http://localhost:{self.port}")
        
        # Abre no navegador
        webbrowser.open(f'http://localhost:{self.port}')
    
    def _run(self):
        while self.running:
            self.server.handle_request()
    
    def stop(self):
        self.running = False
        if self.server:
            self.server.shutdown()


# Singleton
_server = None

def get_server(port=8888) -> DashboardServer:
    global _server
    if _server is None:
        _server = DashboardServer(port)
    return _server

def update_data(services=None):
    _dashboard_data.update(services)


if __name__ == "__main__":
    server = DashboardServer()
    server.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
