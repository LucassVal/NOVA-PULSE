"""
NovaPulse Standby Memory Cleaner v2.2
Purges Windows standby memory (cached file pages) to free RAM.

Similar to ISLC (Intelligent Standby List Cleaner) but integrated.

Design Decisions:
  - Only purges StandbyList (code 4). Never calls EmptyWorkingSets (code 2)
    because that forces active apps to swap to disk, causing 1-2s stutter.
  - Surgical check: Only cleans if BOTH conditions are true:
      1. Available RAM < threshold (default 3GB)
      2. Standby cache > 1GB (cleaning empty cache = wasted I/O)
  - Minimum 30 seconds between cleans to prevent thrashing.
  - Tracks total MB cleaned per session for the dashboard.

Uses NtSetSystemInformation via ctypes — requires Administrator.

Target: Intel Core i5-11300H, 16GB RAM (Tiger Lake laptop)
"""
import ctypes
from ctypes import wintypes
import time
import threading
import psutil
from datetime import datetime


# Windows API constants
SystemMemoryListInformation = 80
MemoryPurgeStandbyList = 4
# MemoryEmptyWorkingSets = 2  # DISABLED — causes stutter

# Load Windows DLLs
ntdll = ctypes.WinDLL('ntdll')
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


class StandbyMemoryCleaner:
    """
    Monitors RAM and purges standby list when memory is low.

    Improved in v2.2:
    - Minimum 30s between cleans (prevents thrashing)
    - Logs total freed per session
    - Smarter threshold defaults (3GB instead of 1GB)
    - Standby estimation before cleaning
    """

    def __init__(self, threshold_mb=3072, check_interval=10):
        self.threshold_mb = threshold_mb        # Clean when available < this
        self.check_interval = check_interval     # Seconds between checks
        self.min_clean_interval = 30             # Minimum 30s between cleans
        self.min_standby_mb = 1024               # Only clean if standby > 1GB
        self.running = False
        self.thread = None
        self.last_cleaned_mb = 0
        self.clean_count = 0
        self.total_cleaned_mb = 0
        self._last_clean_time = 0                # Timestamp of last clean
        self._privilege_enabled = False

    def start(self):
        """Start automatic monitoring."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True,
                                       name='NovaPulse-MemCleaner')
        self.thread.start()
        print(f"[MEM] Standby Cleaner started (threshold: {self.threshold_mb}MB, "
              f"interval: {self.check_interval}s)")

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.total_cleaned_mb > 0:
            print(f"[MEM] Session total: {self.total_cleaned_mb}MB freed in {self.clean_count} cleans")
        print("[MEM] Standby Cleaner stopped")

    def _monitoring_loop(self):
        """Main monitoring loop with surgical cleaning."""
        # Enable privilege once at startup
        self._enable_privilege()

        while self.running:
            try:
                mem = psutil.virtual_memory()
                available_mb = mem.available // (1024 * 1024)

                if available_mb < self.threshold_mb:
                    # Check 1: Is there actually standby cache to clean?
                    # (Available - Free = approximate standby cache)
                    standby_estimated = mem.available - mem.free
                    standby_mb = standby_estimated // (1024 * 1024)

                    # Check 2: Min interval between cleans (prevent thrashing)
                    time_since_last = time.time() - self._last_clean_time

                    if standby_mb > self.min_standby_mb and time_since_last >= self.min_clean_interval:
                        freed_mb = self.clean_standby_memory()

                        if freed_mb > 50:
                            self.last_cleaned_mb = freed_mb
                            self.clean_count += 1
                            self.total_cleaned_mb += freed_mb
                            self._last_clean_time = time.time()
                            print(f"[MEM] Purged {freed_mb}MB standby → "
                                  f"{available_mb + freed_mb}MB available "
                                  f"(session total: {self.total_cleaned_mb}MB)")
                    # else: Low memory but nothing to clean, or too soon. Skip.

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"[MEM] Monitoring error: {e}")
                time.sleep(10)

    def clean_standby_memory(self):
        """
        Purge the Windows Standby List.

        This frees cached file pages that Windows keeps "just in case".
        These pages are already marked as available by the OS, but
        some games and apps see them as "used" and allocate more,
        leading to unnecessary paging.

        Returns: MB freed (0 if failed)
        """
        try:
            if not self._privilege_enabled:
                self._enable_privilege()

            mem_before = psutil.virtual_memory().available // (1024 * 1024)

            # Purge StandbyList ONLY
            command = ctypes.c_int(MemoryPurgeStandbyList)
            ntdll.NtSetSystemInformation(
                SystemMemoryListInformation,
                ctypes.byref(command),
                ctypes.sizeof(command)
            )

            # NOTE: We consciously do NOT call MemoryEmptyWorkingSets.
            # While it frees more "RAM", it forces every running process
            # to re-fault its pages from disk, causing 1-2 seconds of
            # system-wide stuttering. Not worth it.

            time.sleep(0.1)  # Brief wait for OS to process

            mem_after = psutil.virtual_memory().available // (1024 * 1024)
            return max(0, mem_after - mem_before)

        except Exception as e:
            print(f"[MEM] Clean error: {e}")
            return 0

    def _enable_privilege(self):
        """Enable SeProfileSingleProcessPrivilege (required for NtSetSystemInformation)."""
        try:
            SE_PRIVILEGE_ENABLED = 0x00000002
            TOKEN_ADJUST_PRIVILEGES = 0x0020
            TOKEN_QUERY = 0x0008

            token = wintypes.HANDLE()
            kernel32.OpenProcessToken(
                kernel32.GetCurrentProcess(),
                TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                ctypes.byref(token)
            )

            luid = wintypes.LUID()
            ctypes.windll.advapi32.LookupPrivilegeValueW(
                None,
                "SeProfileSingleProcessPrivilege",
                ctypes.byref(luid)
            )

            class TOKEN_PRIVILEGES(ctypes.Structure):
                _fields_ = [
                    ("PrivilegeCount", wintypes.DWORD),
                    ("Luid", wintypes.LUID),
                    ("Attributes", wintypes.DWORD),
                ]

            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Luid = luid
            tp.Attributes = SE_PRIVILEGE_ENABLED

            result = ctypes.windll.advapi32.AdjustTokenPrivileges(
                token, False, ctypes.byref(tp),
                ctypes.sizeof(tp), None, None
            )

            kernel32.CloseHandle(token)

            if result:
                self._privilege_enabled = True

        except:
            pass  # Privilege may already be enabled

    def get_memory_info(self):
        """Return current memory info dict for dashboard."""
        mem = psutil.virtual_memory()
        return {
            'total_mb': mem.total // (1024 * 1024),
            'available_mb': mem.available // (1024 * 1024),
            'used_percent': mem.percent
        }


if __name__ == "__main__":
    cleaner = StandbyMemoryCleaner(threshold_mb=3072, check_interval=10)
    cleaner.start()

    try:
        while True:
            mem_info = cleaner.get_memory_info()
            print(f"\rRAM: {mem_info['available_mb']}MB free / {mem_info['total_mb']}MB total "
                  f"({100 - mem_info['used_percent']:.1f}% free) | "
                  f"Cleans: {cleaner.clean_count} | "
                  f"Total freed: {cleaner.total_cleaned_mb}MB", end='')
            time.sleep(2)
    except KeyboardInterrupt:
        cleaner.stop()
        print("\n[INFO] Stopped")
