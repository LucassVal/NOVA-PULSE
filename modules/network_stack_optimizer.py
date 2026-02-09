"""
NovaPulse - Network Stack Optimizer (Extended)
Otimizações avançadas de rede além do QoS básico
Complementa network_qos.py
"""
import winreg
import subprocess
import ctypes
from typing import Dict, Optional


class NetworkStackOptimizer:
    """
    Otimizações avançadas da pilha de rede do Windows
    
    Inclui:
    - TCP/IP stack tweaks
    - Congestion control algorithms
    - ECN (Explicit Congestion Notification)
    - Buffer optimizations
    - Gaming-specific optimizations
    """
    
    TCP_KEY = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    AFD_KEY = r"SYSTEM\CurrentControlSet\Services\AFD\Parameters"
    
    def __init__(self):
        self.is_admin = self._check_admin()
        self.applied_changes = {}
    
    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _set_registry_value(self, key_path: str, value_name: str, value_data, value_type=winreg.REG_DWORD) -> bool:
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            return False
    
    def _run_netsh(self, args: str) -> bool:
        try:
            result = subprocess.run(
                f"netsh {args}",
                shell=True, capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def set_congestion_control(self, algorithm: str = "ctcp") -> bool:
        """
        Define algoritmo de controle de congestionamento TCP
        
        Algorithms:
        - "ctcp": Compound TCP (recomendado para Windows, bom para jogos)
        - "cubic": CUBIC (melhor para conexões de alta latência)
        - "dctcp": Data Center TCP (para redes empresariais)
        - "newreno": Default antigo
        """
        if not self.is_admin:
            return False
        
        success = self._run_netsh(f"int tcp set supplemental template=internet congestionprovider={algorithm}")
        
        if success:
            print(f"[NETSTACK] ✓ Congestion Control = {algorithm}")
            self.applied_changes['congestion'] = algorithm
        else:
            print(f"[NETSTACK] ℹ Congestion Control: usando padrão do sistema")
        
        return success
    
    def enable_ecn(self, enable: bool = True) -> bool:
        """
        Habilita ECN (Explicit Congestion Notification)
        
        ECN permite que roteadores notifiquem congestionamento sem dropar pacotes.
        Pode melhorar performance em redes congestionadas.
        """
        if not self.is_admin:
            return False
        
        value = "enabled" if enable else "disabled"
        success = self._run_netsh(f"int tcp set global ecncapability={value}")
        
        if success:
            state = "habilitado" if enable else "desabilitado"
            print(f"[NETSTACK] ✓ ECN {state}")
            self.applied_changes['ecn'] = enable
        
        return success
    
    def set_receive_side_scaling(self, enable: bool = True) -> bool:
        """
        Configura RSS (Receive Side Scaling)
        
        RSS distribui processamento de rede entre múltiplos cores.
        Melhora performance em conexões de alta velocidade.
        """
        if not self.is_admin:
            return False
        
        value = "enabled" if enable else "disabled"
        success = self._run_netsh(f"int tcp set global rss={value}")
        
        if success:
            state = "habilitado" if enable else "desabilitado"
            print(f"[NETSTACK] ✓ RSS {state}")
            self.applied_changes['rss'] = enable
        
        return success
    
    def set_auto_tuning_level(self, level: str = "normal") -> bool:
        """
        Configura Auto-Tuning de janela TCP
        
        Levels:
        - "disabled": Janela fixa (pode ajudar em redes instáveis)
        - "highlyrestricted": Muito conservador
        - "restricted": Conservador  
        - "normal": Balanço (recomendado)
        - "experimental": Agressivo
        """
        if not self.is_admin:
            return False
        
        success = self._run_netsh(f"int tcp set global autotuninglevel={level}")
        
        if success:
            print(f"[NETSTACK] ✓ Auto-Tuning = {level}")
            self.applied_changes['autotuning'] = level
        
        return success
    
    def disable_tcp_timestamps(self) -> bool:
        """
        Desativa TCP Timestamps
        
        Timestamps são usados para RTT measurement.
        Desativar pode reduzir overhead em alguns casos.
        """
        if not self.is_admin:
            return False
        
        success = self._run_netsh("int tcp set global timestamps=disabled")
        
        if success:
            print("[NETSTACK] ✓ TCP Timestamps desativados")
            self.applied_changes['timestamps'] = False
        
        return success
    
    def set_tcp_initial_rto(self, rto_ms: int = 2000) -> bool:
        """
        Define Initial RTO (Retransmission Timeout)
        
        Menor valor = retransmissão mais rápida (bom para gaming)
        Valor padrão: 3000ms
        Recomendado gaming: 2000ms
        """
        if not self.is_admin:
            return False
        
        success = self._run_netsh(f"int tcp set global initialRto={rto_ms}")
        
        if success:
            print(f"[NETSTACK] ✓ Initial RTO = {rto_ms}ms")
            self.applied_changes['initial_rto'] = rto_ms
        
        return success
    
    def set_max_syn_retransmissions(self, count: int = 2) -> bool:
        """
        Define máximo de retransmissões SYN
        
        Menos retransmissões = falha mais rápida em conexões problemáticas
        Padrão: 2
        """
        if not self.is_admin:
            return False
        
        success = self._run_netsh(f"int tcp set global maxsynretransmissions={count}")
        
        if success:
            print(f"[NETSTACK] ✓ Max SYN Retransmissions = {count}")
            self.applied_changes['max_syn'] = count
        
        return success
    
    def optimize_default_ttl(self) -> bool:
        """
        Otimiza TTL padrão para melhor roteamento
        """
        if not self.is_admin:
            return False
        
        # TTL padrão: 128 (Windows), pode aumentar para 64 hops
        success = self._set_registry_value(self.TCP_KEY, "DefaultTTL", 64)
        
        if success:
            print("[NETSTACK] ✓ Default TTL = 64")
            self.applied_changes['ttl'] = 64
        
        return success
    
    def optimize_afd_buffers(self) -> bool:
        """
        Otimiza buffers do AFD (Ancillary Function Driver)
        AFD é responsável pelo socket layer do Windows
        """
        if not self.is_admin:
            return False
        
        # Aumenta buffers para melhor throughput
        # DefaultReceiveWindow e DefaultSendWindow
        success1 = self._set_registry_value(self.AFD_KEY, "DefaultReceiveWindow", 65535)
        success2 = self._set_registry_value(self.AFD_KEY, "DefaultSendWindow", 65535)
        
        # FastSendDatagramThreshold
        success3 = self._set_registry_value(self.AFD_KEY, "FastSendDatagramThreshold", 1024)
        
        if success1 or success2 or success3:
            print("[NETSTACK] ✓ AFD buffers otimizados")
            self.applied_changes['afd_buffers'] = True
        
        return success1 or success2
    
    def disable_network_throttling(self) -> bool:
        """
        Desativa throttling de rede durante reprodução de mídia
        (Complementa configuração em MMCSS)
        """
        if not self.is_admin:
            return False
        
        mm_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        success = self._set_registry_value(mm_key, "NetworkThrottlingIndex", 0xFFFFFFFF)
        
        if success:
            print("[NETSTACK] ✓ Network Throttling desativado")
            self.applied_changes['throttling'] = False
        
        return success
    
    def apply_all_optimizations(self, gaming_mode: bool = True) -> Dict[str, bool]:
        """
        Aplica todas as otimizações de rede
        
        gaming_mode: Otimiza para menor latência
        """
        print("\n[NETSTACK] Aplicando otimizações de rede avançadas...")
        
        results = {}
        
        # Congestion control
        results['congestion'] = self.set_congestion_control("ctcp")
        
        # ECN
        results['ecn'] = self.enable_ecn(True)
        
        # RSS
        results['rss'] = self.set_receive_side_scaling(True)
        
        if gaming_mode:
            # Gaming: Normal auto-tuning
            results['autotuning'] = self.set_auto_tuning_level("normal")
            results['rto'] = self.set_tcp_initial_rto(2000)
            results['max_syn'] = self.set_max_syn_retransmissions(2)
        else:
            results['autotuning'] = self.set_auto_tuning_level("normal")
        
        # Otimizações gerais
        results['ttl'] = self.optimize_default_ttl()
        results['afd'] = self.optimize_afd_buffers()
        results['throttling'] = self.disable_network_throttling()
        
        success_count = sum(results.values())
        print(f"[NETSTACK] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, any]:
        """Retorna status atual das configurações de rede"""
        status = {}
        
        try:
            result = subprocess.run(
                "netsh int tcp show global",
                shell=True, capture_output=True, text=True
            )
            
            output = result.stdout.lower()
            
            if "rss" in output:
                status['rss'] = "enabled" in output.split("rss")[1][:50]
            
            if "ecn" in output:
                status['ecn'] = "enabled" in output.split("ecn")[1][:50]
                
        except:
            pass
        
        return status


# Singleton
_instance = None

def get_optimizer() -> NetworkStackOptimizer:
    global _instance
    if _instance is None:
        _instance = NetworkStackOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = NetworkStackOptimizer()
    print("Status:", optimizer.get_status())
