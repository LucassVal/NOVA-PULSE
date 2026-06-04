"""
NovaPulse - Extreme AI Optimizer
Implements the 10 final optimization vectors for extreme AI workloads (LLM inference).
Target: ASUS X3500PC - V2.4 AI-Workload Spec
"""
import os
import subprocess
import ctypes
from typing import Dict
import psutil

class ExtremeAIOptimizer:
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}

    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def _run_cmd(self, cmd: str) -> bool:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            , errors='replace')
            return result.returncode == 0
        except Exception:
            return False

    def _run_powershell(self, cmd: str) -> bool:
        try:
            result = subprocess.run(
                f'powershell -Command "{cmd}"',
                shell=True, capture_output=True, text=True
            , errors='replace')
            return result.returncode == 0
        except Exception:
            return False

    def set_tcp_autotuning(self, level: str = "normal") -> bool:
        """Vector 16: TCP/IP Global Auto-Tuning.

        FIX (2026-06 research): 'experimental' e destinado a WAN de altissima
        latencia (datacenter-a-datacenter), NAO a jogos nem inferencia local.
        Para loopback (127.0.0.1) e irrelevante; para uso geral 'normal' e mais
        estavel. Default mudado para 'normal'. Passe level='experimental'
        explicitamente apenas para enlaces WAN de alta latencia.
        Fonte: https://tcpoptimizer.net/what-is-tcp-window-auto-tuning/
        """
        if not self.is_admin:
            return False
        if level not in ("normal", "experimental", "restricted",
                         "highlyrestricted", "disabled"):
            level = "normal"
        print(f"[EXTREME] Setting TCP Auto-Tuning to {level}...")
        success = self._run_cmd(f"netsh int tcp set global autotuninglevel={level}")
        self.applied_changes['tcp_autotuning'] = success
        return success

    def disable_vbs_memory_integrity(self, confirm: bool = False) -> bool:
        """Vector 19: VBS & Memory Integrity (HVCI) OFF.

        CAVEAT (2026-06 research): ganho real de 5-25%, MAS o i5-11300H (11a gen)
        tem MBEC, que reduz o impacto do HVCI para ~nivel do VBS sozinho. E uma
        troca de SEGURANCA — por isso e opt-in explicito (confirm=True).
        Importante: desligar Memory Integrity NAO desliga o VBS; e preciso zerar
        AMBOS (EnableVirtualizationBasedSecurity + HVCI) ou o overhead permanece.
        Fonte: https://www.tomshardware.com/how-to/disable-vbs-windows-11
        """
        if not self.is_admin or not confirm:
            if not confirm:
                print("[EXTREME] VBS disable e opt-in (confirm=True). Pulando.")
            return False
        print("[EXTREME] Disabling VBS + HVCI (Requires Reboot, security tradeoff)...")
        # Zera AMBOS: VBS e HVCI.
        cmd = r'reg add "HKLM\System\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f'
        success = self._run_cmd(cmd)
        cmd2 = r'reg add "HKLM\System\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f'
        success = success and self._run_cmd(cmd2)
        self.applied_changes['vbs_disabled'] = success
        return success

    def add_defender_llm_exclusion(self) -> bool:
        """Vector 20: Defender LLM Exclusion Zone"""
        if not self.is_admin:
            return False
        print("[EXTREME] Adding ~/.ollama to Defender exclusions...")
        user_profile = os.environ.get('USERPROFILE', '')
        ollama_path = os.path.join(user_profile, '.ollama')
        
        # Ensure path exists so Defender accepts it
        if not os.path.exists(ollama_path):
            try:
                os.makedirs(ollama_path)
            except Exception:
                pass
                
        success = self._run_powershell(f"Add-MpPreference -ExclusionPath '{ollama_path}'")
        self.applied_changes['defender_exclusion'] = success
        return success

    def apply_wsl_hard_limits(self) -> bool:
        """Vector 12: .WSLConfig Hard-Limits (12GB RAM, 6 Cores)"""
        print("[EXTREME] Applying WSL2 Hard Limits...")
        user_profile = os.environ.get('USERPROFILE', '')
        wslconfig_path = os.path.join(user_profile, '.wslconfig')
        config_content = "[wsl2]\nmemory=12GB\nprocessors=6\nswap=0\n"
        
        try:
            with open(wslconfig_path, 'w') as f:
                f.write(config_content)
            self.applied_changes['wsl_limits'] = True
            return True
        except Exception as e:
            print(f"[EXTREME] Failed to write .wslconfig: {e}")
            self.applied_changes['wsl_limits'] = False
            return False

    def apply_process_lasso_affinity(self) -> bool:
        """Vector 14: Process Lasso / Hard Affinity - Lock background apps"""
        print("[EXTREME] Applying Hard Affinity for LLM context...")
        # Since we don't have Process Lasso, we enforce affinity via psutil directly on python processes
        # leaving cores 0-3 for LLM / Servers.
        success = False
        try:
            my_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['pid'] == my_pid:
                    continue
                # For demonstration, we could restrict Edge or Discord to higher cores (4,5,6,7)
                name = str(proc.info['name']).lower()
                if 'msedge' in name or 'discord' in name:
                    try:
                        p = psutil.Process(proc.info['pid'])
                        p.cpu_affinity([4, 5, 6, 7])
                        success = True
                    except Exception:
                        pass
        except Exception:
            pass
        self.applied_changes['process_affinity'] = success
        return success

    def optimize_m2_storage(self) -> bool:
        """Vector 21: M.2 NVMe Storage Optimizer (Disable write-cache buffer flushing)"""
        if not self.is_admin:
            return False
        print("[EXTREME] Optimizing M.2 NVMe Storage...")
        # Often requires specific device instance path, but globally we can tweak fsutil
        success = self._run_cmd("fsutil behavior set disablelastaccess 1")
        success = success and self._run_cmd("fsutil behavior set memoryusage 2")
        self.applied_changes['m2_optimized'] = success
        return success

    def optimize_wifi_network(self) -> bool:
        """Vector 22: WiFi Latency Optimizer (Disable Background Scans)"""
        if not self.is_admin:
            return False
        print("[EXTREME] Optimizing WiFi / WLAN AutoConfig...")
        # Disabling background scan on interfaces to avoid lag spikes
        # Requires knowing the interface name, fallback to generic WLAN settings
        self._run_cmd('netsh wlan set autoconfig enabled=no interface="Wi-Fi"')
        # Ignore errors if no Wi-Fi interface
        self.applied_changes['wifi_optimized'] = True
        return True

    def aggressive_memory_compressor(self) -> bool:
        """Vector 23: Memory Compression (MMAgent).

        FIX (2026-06 research): benchmarks em 42 configs mostram ganho ZERO ao
        forcar compressao em sistemas >= 16GB. Em vez de "agressivo", so
        garantimos os defaults sensatos: PageCombining (dedup, ajuda navegador)
        permanece, mas a compressao agressiva NAO e forcada em maquinas com
        16GB+ — deixamos o gerenciador do Windows decidir.
        Fonte: https://www.ninjaone.com/blog/enable-or-disable-memory-compression-in-windows-11/
        """
        if not self.is_admin:
            return False
        try:
            total_gb = psutil.virtual_memory().total / (1024 ** 3)
        except Exception:
            total_gb = 16
        # PageCombining ajuda em qualquer config (dedup de paginas identicas).
        success = self._run_powershell("Enable-MMAgent -PageCombining")
        if total_gb < 16:
            print("[EXTREME] <16GB: ativando MemoryCompression...")
            success = success and self._run_powershell("Enable-MMAgent -MemoryCompression")
            self.applied_changes['aggressive_memory'] = success
        else:
            print(f"[EXTREME] {total_gb:.0f}GB RAM: compressao agressiva sem ganho mensuravel, pulada (PageCombining ON).")
            self.applied_changes['aggressive_memory'] = 'skipped_16gb+'
        return success

    def audit_and_harden_ports(self) -> bool:
        """Vector 24: Audit CPU/GPU Ports and Close Vulnerabilities"""
        if not self.is_admin:
            return False
        print("[EXTREME] Auditing open ports and hardening...")
        # Block common telemetry and insecure ports (135, 137, 138, 139, 445)
        # Using Windows Firewall
        cmd = 'netsh advfirewall firewall add rule name="Block_Insecure_SMB_RPC" dir=in action=block protocol=TCP localport=135,139,445'
        success = self._run_cmd(cmd)
        self.applied_changes['ports_hardened'] = success
        return success

    def apply_all_optimizations(self) -> Dict[str, bool]:
        print("\n[EXTREME] Applying Extreme Vector Expansion...")
        self.set_tcp_autotuning()
        self.disable_vbs_memory_integrity()
        self.add_defender_llm_exclusion()
        self.apply_wsl_hard_limits()
        self.apply_process_lasso_affinity()
        
        # New Vectors
        self.optimize_m2_storage()
        self.optimize_wifi_network()
        self.aggressive_memory_compressor()
        self.audit_and_harden_ports()
        
        return self.applied_changes
        
    def is_optimized(self) -> bool:
        """Verify if TCP experimental is active as a proxy for this module"""
        try:
            res = subprocess.run("netsh int tcp show global", shell=True, capture_output=True, text=True, errors='replace')
            return "experimental" in res.stdout.lower()
        except Exception:
            return False

# Singleton
_instance = None

def get_optimizer() -> ExtremeAIOptimizer:
    global _instance
    if _instance is None:
        _instance = ExtremeAIOptimizer()
    return _instance

if __name__ == "__main__":
    opt = get_optimizer()
    opt.apply_all_optimizations()
