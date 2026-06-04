"""
NovaPulse - Dynamic Scheduler v1.0
ProBalance algorithm: prioridade por demanda real de CPU, nao por nome.
APIs: SetPriorityClass + EcoQoS (PROCESS_POWER_THROTTLING_STATE)

Referencias:
  https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation
  https://devblogs.microsoft.com/performance-diagnostics/introducing-ecoqos/
"""
import ctypes
import ctypes.wintypes
import threading
import time
import psutil
from collections import deque, defaultdict

kernel32 = ctypes.windll.kernel32

ABOVE_NORMAL  = 0x00008000
NORMAL        = 0x00000020
BELOW_NORMAL  = 0x00004000

ProcessPowerThrottling              = 4
PROCESS_POWER_THROTTLING_VERSION    = 1
PROCESS_POWER_THROTTLING_EXEC_SPEED = 0x1
PROCESS_SET_INFORMATION             = 0x0200

CPU_COUNT = psutil.cpu_count(logical=True) or 8


class _PPTS(ctypes.Structure):
    _fields_ = [
        ("Version",     ctypes.c_ulong),
        ("ControlMask", ctypes.c_ulong),
        ("StateMask",   ctypes.c_ulong),
    ]


SYSTEM_PROCS = {
    "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "dwm.exe", "winlogon.exe",
    "fontdrvhost.exe", "audiodg.exe", "explorer.exe", "taskhostw.exe",
    "sihost.exe", "runtimebroker.exe", "searchhost.exe",
}

PROTECTED_AI = {
    "ollama.exe", "ollama_llama_server.exe",
    "novapulse.exe", "antigravity.exe",
}


def _adjust(pid: int, priority: int, ecoqos: bool) -> None:
    handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
    if not handle:
        return
    try:
        kernel32.SetPriorityClass(handle, priority)
        state = _PPTS(
            Version=PROCESS_POWER_THROTTLING_VERSION,
            ControlMask=PROCESS_POWER_THROTTLING_EXEC_SPEED,
            StateMask=PROCESS_POWER_THROTTLING_EXEC_SPEED if ecoqos else 0,
        )
        kernel32.SetProcessInformation(
            handle,
            ProcessPowerThrottling,
            ctypes.byref(state),
            ctypes.sizeof(state),
        )
    except Exception:
        pass
    finally:
        kernel32.CloseHandle(handle)


class DynamicScheduler:
    """
    Monitora todos os processos por demanda real de CPU (cpu_times delta).
    Aplica ABOVE_NORMAL + EcoQoS OFF para quem esta trabalhando.
    Aplica BELOW_NORMAL + EcoQoS ON  para quem esta ocioso.
    Processos AI (ollama, antigravity) nunca ficam abaixo de NORMAL.
    """

    SAMPLE_INTERVAL = 1.0
    WINDOW          = 5
    BURST_THRESH    = 0.15
    IDLE_THRESH     = 0.03
    HYSTERESIS      = 3

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.SAMPLE_INTERVAL = float(cfg.get("sample_interval", self.SAMPLE_INTERVAL))
        self.WINDOW          = int(cfg.get("window_size",    self.WINDOW))
        self.BURST_THRESH    = float(cfg.get("burst_threshold", self.BURST_THRESH))
        self.IDLE_THRESH     = float(cfg.get("idle_threshold",  self.IDLE_THRESH))
        self.HYSTERESIS      = int(cfg.get("hysteresis",    self.HYSTERESIS))

        self.running  = False
        self._thread  = None
        self._hist    = defaultdict(lambda: deque(maxlen=self.WINDOW))
        self._burst   = defaultdict(int)
        self._idle    = defaultdict(int)
        self._state   = {}
        self._cpu1    = {}
        self._t1      = 0.0

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._prime()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(
            f"[DSCH] Dynamic Scheduler iniciado "
            f"(burst={self.BURST_THRESH}, idle={self.IDLE_THRESH}, "
            f"hyst={self.HYSTERESIS}, window={self.WINDOW}s)"
        )

    def stop(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _prime(self) -> None:
        self._t1 = time.monotonic()
        for proc in psutil.process_iter(["pid"]):
            try:
                ct = proc.cpu_times()
                self._cpu1[proc.pid] = ct.user + ct.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def _loop(self) -> None:
        while self.running:
            time.sleep(self.SAMPLE_INTERVAL)
            try:
                self._sample()
            except Exception:
                pass

    def _sample(self) -> None:
        t2      = time.monotonic()
        elapsed = t2 - self._t1
        if elapsed < 0.1:
            return

        cpu2: dict[int, tuple[str, float]] = {}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                ct = proc.cpu_times()
                cpu2[proc.pid] = (
                    (proc.info["name"] or "").lower(),
                    ct.user + ct.system,
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        for pid, (name, c2) in cpu2.items():
            if name in SYSTEM_PROCS:
                continue
            c1    = self._cpu1.get(pid, c2)
            delta = (c2 - c1) / elapsed / CPU_COUNT
            self._hist[pid].append(delta)
            avg   = sum(self._hist[pid]) / len(self._hist[pid])

            if avg > self.BURST_THRESH:
                self._burst[pid] += 1
                self._idle[pid]   = 0
            elif avg < self.IDLE_THRESH:
                self._idle[pid]  += 1
                self._burst[pid]  = 0
            else:
                self._burst[pid] = max(0, self._burst[pid] - 1)
                self._idle[pid]  = max(0, self._idle[pid]  - 1)

            self._act(pid, name)

        self._cpu1 = {pid: v[1] for pid, v in cpu2.items()}
        self._t1   = t2

        alive = set(cpu2)
        for mapping in (self._hist, self._burst, self._idle, self._state):
            for key in list(mapping):
                if key not in alive:
                    del mapping[key]

    def _act(self, pid: int, name: str) -> None:
        current = self._state.get(pid, "normal")
        is_ai   = name in PROTECTED_AI

        if self._burst[pid] >= self.HYSTERESIS and current != "burst":
            _adjust(pid, ABOVE_NORMAL, False)
            self._state[pid] = "burst"

        elif self._idle[pid] >= self.HYSTERESIS and current != "idle":
            priority = NORMAL if is_ai else BELOW_NORMAL
            _adjust(pid, priority, not is_ai)
            self._state[pid] = "idle"

    def get_stats(self) -> dict:
        return {
            "burst": sum(1 for v in self._state.values() if v == "burst"),
            "idle":  sum(1 for v in self._state.values() if v == "idle"),
            "total": len(self._state),
        }


_instance: DynamicScheduler | None = None


def get_scheduler(config: dict | None = None) -> DynamicScheduler:
    global _instance
    if _instance is None:
        _instance = DynamicScheduler(config)
    return _instance
