"""
NovaPulse - Dynamic Scheduler v2.0 (ProBalance-style, contention-gated)
Prioridade por demanda real de CPU, nao por nome — seguindo o modelo correto:
REBAIXAR o background concorrente apenas sob contencao real, em vez de
PROMOVER cegamente tudo que demanda CPU.

Auditoria (2026-06) vs Process Lasso / ProBalance:
  - O modelo antigo promovia para HIGH qualquer processo com burst > 15% de CPU,
    sem gate de contencao. Sob carga de LLM TUDO bursta -> tudo virava HIGH ->
    zero diferenciacao e risco de inanicao do sistema.
  - Best practice: so intervir quando ha disputa real (CPU total > LOAD_GATE por
    ~2.8s) e entao REBAIXAR o processo de background que consome, NUNCA promover
    tudo. O processo em foco (foreground) e os processos AI sao protegidos.
  - Mudancas sao temporarias e revertidas quando a contencao passa.

APIs: SetPriorityClass + EcoQoS (PROCESS_POWER_THROTTLING_STATE) +
      GetForegroundWindow (deteccao de foreground).

Referencias:
  https://bitsum.com/how-probalance-works/
  https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation
  https://devblogs.microsoft.com/performance-diagnostics/introducing-ecoqos/
"""
import time
import threading
import ctypes
import ctypes.wintypes
from typing import Dict
from collections import deque, defaultdict
from enum import IntEnum

try:
    import psutil
except ImportError:
    psutil = None

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

PROCESS_SET_INFORMATION             = 0x0200
ProcessPowerThrottling              = 4
PROCESS_POWER_THROTTLING_VERSION    = 1
PROCESS_POWER_THROTTLING_EXEC_SPEED = 0x1

CPU_COUNT = (psutil.cpu_count(logical=True) if psutil else 8) or 8


class PriorityClass(IntEnum):
    IDLE = 0x40
    BELOW_NORMAL = 0x4000
    NORMAL = 0x20
    ABOVE_NORMAL = 0x8000
    HIGH = 0x80
    REALTIME = 0x100


class _PPTS(ctypes.Structure):
    _fields_ = [
        ("Version",     ctypes.c_ulong),
        ("ControlMask", ctypes.c_ulong),
        ("StateMask",   ctypes.c_ulong),
    ]


SYSTEM_PROCS = {
    "system idle process", "system", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "dwm.exe",
    "winlogon.exe", "fontdrvhost.exe", "audiodg.exe", "explorer.exe",
    "taskhostw.exe", "sihost.exe", "runtimebroker.exe", "searchhost.exe",
    "memcompression",
}

# Processos AI / inferencia / IDE — nunca rebaixados.
PROTECTED_AI = {
    "ollama.exe", "ollama_llama_server.exe", "llama-server.exe",
    "python.exe", "pythonw.exe",
    "novapulse.exe", "antigravity.exe", "code.exe",
}


def _set_priority(pid: int, priority: int, ecoqos: bool = False) -> bool:
    """Aplica priority class + EcoQoS a um PID. Retorna True se ok."""
    handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
    if not handle:
        return False
    ok = False
    try:
        ok = bool(kernel32.SetPriorityClass(handle, priority))
        state = _PPTS(
            Version=PROCESS_POWER_THROTTLING_VERSION,
            ControlMask=PROCESS_POWER_THROTTLING_EXEC_SPEED,
            StateMask=PROCESS_POWER_THROTTLING_EXEC_SPEED if ecoqos else 0,
        )
        kernel32.SetProcessInformation(
            handle, ProcessPowerThrottling,
            ctypes.byref(state), ctypes.sizeof(state),
        )
    except Exception:
        pass
    finally:
        kernel32.CloseHandle(handle)
    return ok


def _foreground_pid() -> int:
    """PID dono da janela em foreground (0 se indisponivel)."""
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return 0
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)
    except Exception:
        return 0


class DynamicScheduler:
    """
    Modelo ProBalance (contention-gated):
      1. Mede CPU total do sistema em janela rolante.
      2. So intervem quando CPU total > LOAD_GATE por >= GATE_HOLD amostras.
      3. Sob contencao, REBAIXA processos de background que consomem
         (> HOG_THRESH de 1 core) para BELOW_NORMAL + EcoQoS — exceto AI/foreground.
      4. O foreground recebe ABOVE_NORMAL (responsividade), sem EcoQoS.
      5. Quando a contencao passa, restaura todos para NORMAL.

    Compat: expoe promoted_pids/high_count/low_count para o dashboard.
    """

    def __init__(self, load_gate: float = 85.0, window_size: int = 5,
                 check_interval: int = 1, hog_threshold: float = 0.12,
                 gate_hold: int = 3, hysteresis: int = 2):
        self.load_gate = load_gate
        self.window_size = window_size
        self.check_interval = check_interval
        self.hog_threshold = hog_threshold
        self.gate_hold = gate_hold
        self.hysteresis = hysteresis

        self.running = False
        self.monitor_thread = None
        self._hist: Dict[int, deque] = {}
        self._hog: Dict[int, int] = defaultdict(int)
        self._demoted: Dict[int, bool] = {}
        self._cpu1: Dict[int, float] = {}
        self._t1 = 0.0
        self._load_hist = deque(maxlen=gate_hold)
        self._contended = False
        self._fg_pid = 0
        self._fg_boosted = 0

        # Compat dashboard
        self.promoted_pids: set = set()

    # ── Compat properties (dashboard le high_count/low_count) ──
    @property
    def high_count(self) -> int:
        return self._fg_boosted

    @property
    def low_count(self) -> int:
        return len(self._demoted)

    def _prime(self):
        self._t1 = time.monotonic()
        for proc in psutil.process_iter(["pid"]):
            try:
                ct = proc.cpu_times()
                self._cpu1[proc.pid] = ct.user + ct.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def _monitoring_loop(self):
        if not psutil:
            return
        self._prime()
        while self.running:
            time.sleep(self.check_interval)
            try:
                self._sample()
            except Exception:
                pass

    def _sample(self):
        t2 = time.monotonic()
        elapsed = t2 - self._t1
        if elapsed < 0.1:
            return

        total_load = psutil.cpu_percent(interval=0)
        self._load_hist.append(total_load)
        self._fg_pid = _foreground_pid()

        was_contended = self._contended
        self._contended = (
            len(self._load_hist) >= self.gate_hold
            and all(v >= self.load_gate for v in self._load_hist)
        )
        if was_contended and not self._contended:
            self._restore_all()

        cpu2: Dict[int, tuple] = {}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                ct = proc.cpu_times()
                cpu2[proc.pid] = ((proc.info["name"] or "").lower(),
                                  ct.user + ct.system)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self._fg_boosted = 0
        if self._contended:
            for pid, (name, c2) in cpu2.items():
                if name in SYSTEM_PROCS or pid <= 4:
                    continue
                c1 = self._cpu1.get(pid, c2)
                delta = (c2 - c1) / elapsed / CPU_COUNT
                self._hist.setdefault(pid, deque(maxlen=self.window_size)).append(delta)
                avg = sum(self._hist[pid]) / len(self._hist[pid])
                self._act(pid, name, avg)

        self._cpu1 = {pid: v[1] for pid, v in cpu2.items()}
        self._t1 = t2

        alive = set(cpu2)
        for mapping in (self._hist, self._hog):
            for key in list(mapping):
                if key not in alive:
                    del mapping[key]
        for pid in list(self._demoted):
            if pid not in alive:
                del self._demoted[pid]

    def _act(self, pid: int, name: str, avg: float):
        # Foreground (nao-AI): garante responsividade.
        if pid == self._fg_pid and name not in PROTECTED_AI:
            _set_priority(pid, PriorityClass.ABOVE_NORMAL, False)
            self._fg_boosted += 1
            return

        if name in PROTECTED_AI:
            if self._demoted.pop(pid, None):
                _set_priority(pid, PriorityClass.NORMAL, False)
            return

        # Background consumindo CPU sob contencao -> rebaixa (com histerese).
        if avg > self.hog_threshold:
            self._hog[pid] += 1
            if self._hog[pid] >= self.hysteresis and pid not in self._demoted:
                if _set_priority(pid, PriorityClass.BELOW_NORMAL, True):
                    self._demoted[pid] = True
        else:
            self._hog[pid] = max(0, self._hog[pid] - 1)
            if self._hog[pid] == 0 and self._demoted.pop(pid, None):
                _set_priority(pid, PriorityClass.NORMAL, False)

    def _restore_all(self):
        for pid in list(self._demoted):
            _set_priority(pid, PriorityClass.NORMAL, False)
        self._demoted.clear()
        self._hog.clear()

    def get_stats(self) -> dict:
        return {
            "contended": self._contended,
            "demoted": len(self._demoted),
            "fg_boosted": self._fg_boosted,
            "load_gate": self.load_gate,
            "fg_pid": self._fg_pid,
        }

    def get_status(self) -> dict:
        return {"active": self.running, **self.get_stats()}

    def start(self):
        if not psutil:
            print("[SCHEDULER] x psutil not available")
            return False
        if self.running:
            return True
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[SCHEDULER] v2 ProBalance ativo (gate={self.load_gate}% "
              f"hold={self.gate_hold}, hog={self.hog_threshold})")
        return True

    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self._restore_all()
        print("[SCHEDULER] Monitoring stopped")


_instance = None


def get_scheduler() -> DynamicScheduler:
    global _instance
    if _instance is None:
        _instance = DynamicScheduler()
    return _instance


if __name__ == "__main__":
    scheduler = DynamicScheduler()
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
