"""
NovaPulse - Process Controller (Process Lasso Style)
Advanced process control with persistent affinity and priority
"""
import os
import json
import threading
import time
import ctypes
from ctypes import wintypes
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import IntEnum

try:
    import psutil
except ImportError:
    psutil = None


# Windows Priority Classes
class PriorityClass(IntEnum):
    IDLE = 0x40
    BELOW_NORMAL = 0x4000
    NORMAL = 0x20
    ABOVE_NORMAL = 0x8000
    HIGH = 0x80
    REALTIME = 0x100


# I/O Priority
class IOPriority(IntEnum):
    VERY_LOW = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3


@dataclass
class ProcessRule:
    """Optimization rule for a process"""
    name: str                          # Executable name (e.g. "chrome.exe")
    cpu_affinity: Optional[int] = None # Core bitmask (None = all)
    priority: Optional[int] = None      # PriorityClass value
    io_priority: Optional[int] = None   # IOPriority value
    power_throttle: bool = False        # Limit power usage
    memory_priority: int = 5            # 0-5, higher = more important
    enabled: bool = True


class ProcessController:
    """
    Advanced process control (Process Lasso style)
    
    Features:
    - Persistent CPU affinity per application
    - Persistent priority per application
    - Automatic rules for games/browsers/background
    - I/O Priority control
    - Memory Priority control
    """
    
    # Default rules for common apps
    DEFAULT_RULES = {
        # Browsers - low priority, specific cores
        'chrome.exe': ProcessRule('chrome.exe', priority=PriorityClass.BELOW_NORMAL, io_priority=IOPriority.LOW),
        'firefox.exe': ProcessRule('firefox.exe', priority=PriorityClass.BELOW_NORMAL, io_priority=IOPriority.LOW),
        'msedge.exe': ProcessRule('msedge.exe', priority=PriorityClass.BELOW_NORMAL, io_priority=IOPriority.LOW),
        
        # Background apps
        'discord.exe': ProcessRule('discord.exe', priority=PriorityClass.BELOW_NORMAL),
        'spotify.exe': ProcessRule('spotify.exe', priority=PriorityClass.BELOW_NORMAL),
        'steam.exe': ProcessRule('steam.exe', priority=PriorityClass.BELOW_NORMAL),
        'epicgameslauncher.exe': ProcessRule('epicgameslauncher.exe', priority=PriorityClass.BELOW_NORMAL),
        
        # Updaters - very low priority
        'googledrivesync.exe': ProcessRule('googledrivesync.exe', priority=PriorityClass.IDLE, io_priority=IOPriority.VERY_LOW),
        'onedrive.exe': ProcessRule('onedrive.exe', priority=PriorityClass.IDLE, io_priority=IOPriority.VERY_LOW),
        'dropbox.exe': ProcessRule('dropbox.exe', priority=PriorityClass.IDLE, io_priority=IOPriority.VERY_LOW),
        
        # Antivirus - normal priority but low I/O
        'msmpeng.exe': ProcessRule('msmpeng.exe', priority=PriorityClass.NORMAL, io_priority=IOPriority.LOW),
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'process_rules.json')
        self.rules: Dict[str, ProcessRule] = dict(self.DEFAULT_RULES)
        self.running = False
        self.monitor_thread = None
        self.managed_pids: Dict[int, str] = {}  # pid -> process name
        self.cpu_count = os.cpu_count() or 4
        
        # Load custom rules
        self._load_rules()
    
    def _load_rules(self):
        """Load saved rules from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for name, rule_data in data.items():
                        self.rules[name.lower()] = ProcessRule(**rule_data)
        except Exception as e:
            print(f"[PROCESS] ⚠ Error loading rules: {e}")
    
    def _save_rules(self):
        """Save rules to JSON file"""
        try:
            data = {}
            for name, rule in self.rules.items():
                if rule not in self.DEFAULT_RULES.values():
                    data[name] = asdict(rule)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[PROCESS] ⚠ Error saving rules: {e}")
    
    def add_rule(self, rule: ProcessRule):
        """Add a process rule"""
        self.rules[rule.name.lower()] = rule
        self._save_rules()
        print(f"[PROCESS] ✓ Rule added: {rule.name}")
    
    def remove_rule(self, process_name: str):
        """Remove a process rule"""
        name_lower = process_name.lower()
        if name_lower in self.rules:
            del self.rules[name_lower]
            self._save_rules()
            print(f"[PROCESS] ✓ Rule removed: {process_name}")
    
    def _apply_rule_to_process(self, proc, rule: ProcessRule) -> bool:
        """Apply a rule to a process"""
        if not rule.enabled:
            return False
        try:
            pid = proc.pid
            # CPU affinity
            if rule.cpu_affinity is not None:
                proc.cpu_affinity(self._mask_to_list(rule.cpu_affinity))
            # Priority
            if rule.priority is not None:
                PROCESS_SET_INFORMATION = 0x0200
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
                if handle:
                    ctypes.windll.kernel32.SetPriorityClass(handle, rule.priority)
                    ctypes.windll.kernel32.CloseHandle(handle)
            # I/O Priority (requires Windows Vista+)
            if rule.io_priority is not None:
                self._set_io_priority(pid, rule.io_priority)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        except Exception:
            return False
    
    def _mask_to_list(self, mask: int) -> List[int]:
        """Convert bitmask to list of cores"""
        cores = []
        for i in range(self.cpu_count):
            if mask & (1 << i):
                cores.append(i)
        return cores if cores else list(range(self.cpu_count))
    
    def _set_io_priority(self, pid: int, priority: int):
        """Set I/O Priority of a process"""
        try:
            PROCESS_SET_INFORMATION = 0x0200
            ProcessIoPriority = 33
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_SET_INFORMATION, False, pid)
            if handle:
                priority_value = ctypes.c_ulong(priority)
                ctypes.windll.ntdll.NtSetInformationProcess(
                    handle, ProcessIoPriority,
                    ctypes.byref(priority_value), ctypes.sizeof(priority_value)
                )
                ctypes.windll.kernel32.CloseHandle(handle)
        except:
            pass
    
    def _monitoring_loop(self):
        """Process monitoring loop"""
        while self.running:
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        name = proc.info['name'].lower()
                        pid = proc.info['pid']
                        # Check if already managed
                        if pid in self.managed_pids:
                            continue
                        # Look for rule for this process
                        if name in self.rules:
                            rule = self.rules[name]
                            if self._apply_rule_to_process(proc, rule):
                                self.managed_pids[pid] = name
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                # Clean up PIDs that no longer exist
                current_pids = {p.pid for p in psutil.process_iter(['pid'])}
                self.managed_pids = {
                    pid: name for pid, name in self.managed_pids.items()
                    if pid in current_pids
                }
            except Exception:
                pass
            time.sleep(5)  # Check every 5 seconds
    
    def boost_process(self, process_name: str) -> bool:
        """
        Apply temporary boost to a process (for gaming)
        - High priority
        - All cores
        - High I/O
        """
        if not psutil:
            return False
        name_lower = process_name.lower()
        boosted = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == name_lower:
                try:
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
                    proc.cpu_affinity(list(range(self.cpu_count)))
                    boosted = True
                except:
                    pass
        if boosted:
            print(f"[PROCESS] ⚡ Boost applied: {process_name}")
        return boosted
    
    def throttle_background(self) -> int:
        """
        Reduce priority of all background processes
        Returns number of affected processes
        """
        if not psutil:
            return 0
        count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            name = proc.info['name'].lower()
            if name in self.rules:
                try:
                    rule = self.rules[name]
                    if rule.priority and rule.priority < PriorityClass.NORMAL:
                        self._apply_rule_to_process(proc, rule)
                        count += 1
                except:
                    pass
        if count > 0:
            print(f"[PROCESS] ✓ {count} background processes optimized")
        return count
    
    def start(self):
        """Start process monitoring"""
        if not psutil:
            print("[PROCESS] ✗ psutil not available")
            return False
        if self.running:
            return True
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[PROCESS] ✓ Monitoring started ({len(self.rules)} rules)")
        return True
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("[PROCESS] Monitoring stopped")
    
    def get_active_rules(self) -> Dict[str, dict]:
        """Returns active rules and managed processes"""
        return {
            'rules_count': len(self.rules),
            'managed_processes': len(self.managed_pids),
            'rules': {name: asdict(rule) for name, rule in list(self.rules.items())[:10]}
        }
    
    def apply_gaming_preset(self) -> Dict[str, bool]:
        """
        Apply gaming preset:
        - Boost detected game
        - Throttle background
        - Disable unnecessary processes
        """
        print("\n[PROCESS] Applying gaming preset...")
        results = {}
        results['background_throttled'] = self.throttle_background() > 0
        # Detect common running games
        game_keywords = ['game', 'valorant', 'league', 'csgo', 'fortnite', 'apex']
        if psutil:
            for proc in psutil.process_iter(['name']):
                name = proc.info['name'].lower()
                if any(kw in name for kw in game_keywords):
                    results['game_boosted'] = self.boost_process(proc.info['name'])
                    break
        return results


# Singleton
_instance = None

def get_controller() -> ProcessController:
    global _instance
    if _instance is None:
        _instance = ProcessController()
    return _instance


if __name__ == "__main__":
    controller = ProcessController()
    
    print("Default rules:")
    for name, rule in list(controller.rules.items())[:5]:
        print(f"  - {name}: priority={rule.priority}")
    
    print(f"\nTotal: {len(controller.rules)} rules")
