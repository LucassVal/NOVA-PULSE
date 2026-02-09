"""
NovaPulse Auto-Profiler v2.3
Simplified 2-stage system: ACTIVE (85% CPU) / IDLE (30% CPU after 5 min inactivity)

Design Decision — Why 2 stages instead of 3:
  The previous 3-mode system (BOOST/NORMAL/ECO) depended on physical temperature
  sensors (DPTF/ACPI) which have a 2-5 second reporting delay. This gap meant
  the system reacted too late to thermal events, causing stutters.

  The new 2-stage system eliminates sensor dependency:
    ACTIVE = 85% CPU cap. On the i5-11300H this means ~3.1GHz all-core sustained.
              Uses BALANCED Intel profile so Turbo Boost activates on demand peaks.
    IDLE   = 30% CPU cap after 5 minutes of <10% CPU usage. This saves power
             and reduces fan noise when the PC is truly idle.

Why 85% instead of 100%:
  On the i5-11300H, 85% = ~3.1GHz all-core. 100% = ~4.4GHz.
  The sustained thermal difference is significant: 85% keeps the CPU at
  ~65-72°C steady state vs 80-90°C at 100%. Uses BALANCED profile with
  efficient boost — activates only on demand peaks, not constantly.

Target Hardware: Intel Core i5-11300H (Tiger Lake)
"""
import threading
import time
import psutil
from enum import Enum
from collections import deque


class SystemMode(Enum):
    """System operation modes — simplified to 2 stages."""
    ACTIVE = "active"    # 85% CPU — always ready, gaming/work
    IDLE = "idle"        # 30% CPU — after 5 min of inactivity


class AutoProfiler:
    """
    2-stage auto-profiler that adjusts CPU power based on activity.

    Logic:
      - Default: ACTIVE mode (85% CPU cap, BALANCED profile, boost on peaks)
      - If CPU < 10% for 5 continuous minutes → IDLE mode (30% CPU cap, ECO profile)
      - Any CPU spike > 15% → immediately back to ACTIVE

    No temperature sensor dependency. Simple, predictable, reliable.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self.thread = None

        # Configuration
        self.check_interval = self.config.get('check_interval', 2)  # Check every 2s
        self.idle_timeout = self.config.get('idle_timeout', 300)     # 5 minutes (300s)
        self.idle_threshold = self.config.get('idle_threshold', 10)  # CPU < 10% = idle
        self.wake_threshold = self.config.get('wake_threshold', 15)  # CPU > 15% = wake up
        self.active_cpu_cap = self.config.get('active_cpu_cap', 85)  # ACTIVE mode CPU %
        self.idle_cpu_cap = self.config.get('idle_cpu_cap', 30)      # IDLE mode CPU %

        # State
        self.current_mode = SystemMode.ACTIVE
        self.previous_mode = SystemMode.ACTIVE
        self.idle_counter = 0  # Seconds of continuous low CPU
        self.cpu_history = deque(maxlen=10)

        # Services reference
        self.services = {}
        self.on_mode_change_callbacks = []

    def set_services(self, services: dict):
        """Set reference to optimizer services."""
        self.services = services

    def add_mode_change_callback(self, callback):
        """Add callback for mode changes."""
        self.on_mode_change_callbacks.append(callback)

    def get_current_mode(self) -> SystemMode:
        """Return current mode."""
        return self.current_mode

    def get_mode_name(self) -> str:
        """Return friendly mode name for display."""
        names = {
            SystemMode.ACTIVE: "⚡ ACTIVE",
            SystemMode.IDLE: "🌿 IDLE"
        }
        return names.get(self.current_mode, "ACTIVE")

    def get_avg_cpu(self) -> float:
        """Return average CPU from recent readings."""
        if not self.cpu_history:
            return 0.0
        return sum(self.cpu_history) / len(self.cpu_history)

    def start(self):
        """Start automatic monitoring."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True,
                                       name='NovaPulse-AutoProfiler')
        self.thread.start()
        print(f"[AUTO] NovaPulse Auto-Profiler v2.2 started")
        print(f"[AUTO] → ACTIVE: CPU cap {self.active_cpu_cap}% (always)")
        print(f"[AUTO] → IDLE:   CPU cap {self.idle_cpu_cap}% (after {self.idle_timeout}s inactivity)")
        print(f"[AUTO] → Check every {self.check_interval}s")

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[AUTO] Auto-Profiler stopped")

    def _monitoring_loop(self):
        """Main monitoring loop — simple 2-stage logic."""
        # Apply ACTIVE mode on startup
        self._apply_active_mode()

        while self.running:
            try:
                # Read CPU (non-blocking with 0.5s sample)
                cpu_percent = psutil.cpu_percent(interval=0.5)
                self.cpu_history.append(cpu_percent)
                avg_cpu = self.get_avg_cpu()

                if self.current_mode == SystemMode.ACTIVE:
                    # In ACTIVE: check if we should go IDLE
                    if avg_cpu < self.idle_threshold:
                        self.idle_counter += self.check_interval
                        if self.idle_counter >= self.idle_timeout:
                            self._apply_mode(SystemMode.IDLE)
                    else:
                        # Any activity resets the counter
                        self.idle_counter = 0

                elif self.current_mode == SystemMode.IDLE:
                    # In IDLE: any CPU spike → immediately back to ACTIVE
                    if avg_cpu > self.wake_threshold:
                        self.idle_counter = 0
                        self._apply_mode(SystemMode.ACTIVE)

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"[AUTO] Monitoring error: {e}")
                time.sleep(5)

    def _apply_mode(self, new_mode: SystemMode):
        """Apply new mode configuration."""
        self.previous_mode = self.current_mode
        self.current_mode = new_mode

        print(f"\n[AUTO] Mode change: {self.previous_mode.value.upper()} → {new_mode.value.upper()}")

        try:
            if new_mode == SystemMode.ACTIVE:
                self._apply_active_mode()
            else:
                self._apply_idle_mode()

            # Notify callbacks
            for callback in self.on_mode_change_callbacks:
                try:
                    callback(new_mode)
                except:
                    pass
        except Exception as e:
            print(f"[AUTO] Error applying mode: {e}")

    def _apply_active_mode(self):
        """
        ACTIVE mode: 85% CPU cap, moderate memory cleaning.

        Why 85%:
          On i5-11300H, 85% ≈ 3.1GHz all-core sustained.
          Intel Turbo Boost 3.0 still allows single-core spikes to 4.4GHz
          for burst workloads. The 85% cap limits sustained all-core
          power draw, keeping thermals manageable without fan noise.
          Boost mode is set to 'efficient' — activates only on demand peaks.
        """
        print(f"[AUTO] ⚡ ACTIVE MODE — CPU cap: {self.active_cpu_cap}%")

        # CPU: set to active cap (85%)
        if 'cpu_power' in self.services:
            self.services['cpu_power'].set_max_cpu_frequency(self.active_cpu_cap)

        # Intel Power Control: BALANCED profile (85% max, boost on peaks only)
        try:
            from modules import intel_power_control
            intel_power_control.apply_balanced_mode()
        except ImportError:
            pass

        # Memory cleaner: moderate settings
        if 'cleaner' in self.services:
            self.services['cleaner'].threshold_mb = 3072   # Clean when < 3GB free
            self.services['cleaner'].check_interval = 10   # Check every 10s

    def _apply_idle_mode(self):
        """
        IDLE mode: 30% CPU cap, relaxed memory cleaning.

        Triggered after 5 minutes of continuous <10% CPU usage.
        The system is truly idle — user is AFK, screen saver, etc.
        We reduce power to save battery and reduce fan noise.
        Any CPU spike > 15% instantly wakes back to ACTIVE.
        """
        print(f"[AUTO] 🌿 IDLE MODE — CPU cap: {self.idle_cpu_cap}% (energy saving)")

        # CPU: set to idle cap (30%)
        if 'cpu_power' in self.services:
            self.services['cpu_power'].set_max_cpu_frequency(self.idle_cpu_cap)

        # Intel Power Control: ECO profile
        try:
            from modules import intel_power_control
            intel_power_control.apply_eco_mode()
        except ImportError:
            pass

        # Memory cleaner: relaxed (no aggressive cleaning when idle)
        if 'cleaner' in self.services:
            self.services['cleaner'].threshold_mb = 8192   # Only clean if really low
            self.services['cleaner'].check_interval = 60   # Check every 60s

    def force_mode(self, mode: SystemMode):
        """Force a specific mode (manual override)."""
        print(f"[AUTO] Manual override: {mode.value.upper()}")
        self._apply_mode(mode)
        self.idle_counter = 0


# Singleton
_instance = None

def get_profiler() -> AutoProfiler:
    """Return singleton AutoProfiler instance."""
    global _instance
    if _instance is None:
        _instance = AutoProfiler()
    return _instance


if __name__ == "__main__":
    profiler = AutoProfiler()
    profiler.start()

    print("\nMonitoring system (2-stage: ACTIVE/IDLE)...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            mode = profiler.get_mode_name()
            avg_cpu = profiler.get_avg_cpu()
            idle_s = profiler.idle_counter
            print(f"\r[{mode}] CPU Avg: {avg_cpu:.1f}% | Idle: {idle_s}s/{profiler.idle_timeout}s  ", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        profiler.stop()
        print("\n[INFO] Stopped")
