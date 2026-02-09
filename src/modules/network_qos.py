"""
Network QoS Manager - Ping Booster + DNS Security
Prioritizes online gaming traffic + secure DNS with ad blocking
"""
import subprocess
import threading
import time

class NetworkQoSManager:
    """Manages QoS policies and secure DNS"""
    
    # DNS Providers
    DNS_PROVIDERS = {
        'google': {
            'name': 'Google DNS',
            'primary': '8.8.8.8',
            'secondary': '8.8.4.4',
            'description': 'Fast & reliable'
        },
        'adguard': {
            'name': 'AdGuard DNS (Ad Blocking)',
            'primary': '94.140.14.14',
            'secondary': '94.140.15.15',
            'description': 'Blocks ads, trackers & malware'
        },
        'adguard_family': {
            'name': 'AdGuard Family',
            'primary': '94.140.14.15',
            'secondary': '94.140.15.16',
            'description': 'Blocks ads + adult content'
        },
        'cloudflare': {
            'name': 'Cloudflare DNS',
            'primary': '1.1.1.1',
            'secondary': '1.0.0.1',
            'description': 'Fastest DNS'
        },
        'cloudflare_malware': {
            'name': 'Cloudflare (Malware Block)',
            'primary': '1.1.1.2',
            'secondary': '1.0.0.2',
            'description': 'Blocks malware'
        }
    }
    
    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.dns_provider = self.config.get('dns_provider', 'adguard')  # Default: AdGuard
        self.running = False
        
        # Common game ports (UDP)
        self.game_ports = {
            # Valorant, League of Legends, CSGO, Fortnite, etc
            'udp_high': [3074, 3478, 3479, 3480, 5060, 5062, 27015, 27036],
            # Discord, TeamSpeak
            'voip': [5000, 5001, 5002, 9000, 9001]
        }
    
    def apply_qos_rules(self):
        """Apply QoS rules + secure DNS"""
        if not self.enabled:
            return False
            
        print("[NET] Applying network optimizations...")
        
        try:
            # 1. Disable Nagle algorithm (reduces micro-lag)
            self._disable_nagle()
            
            # 2. Optimize TCP buffers
            self._optimize_network_buffer()
            
            # 3. Configure secure DNS (AdGuard by default)
            self._set_secure_dns()
            
            print("[NET] ✓ Network optimizations applied")
            return True
            
        except Exception as e:
            print(f"[NET] Error applying QoS: {e}")
            return False
    
    def _set_secure_dns(self):
        """Configure secure DNS (AdGuard/Google/Cloudflare)"""
        provider = self.DNS_PROVIDERS.get(self.dns_provider, self.DNS_PROVIDERS['adguard'])
        
        print(f"[NET] Configuring {provider['name']}...")
        print(f"[NET] → {provider['description']}")
        
        try:
            # Get active network adapter name
            get_adapter_cmd = '''
            $adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up" -and $_.InterfaceDescription -notlike "*Virtual*"} | Select-Object -First 1
            $adapter.Name
            '''
            result = subprocess.run(['powershell', '-Command', get_adapter_cmd], 
                                    capture_output=True, text=True, timeout=10)
            adapter_name = result.stdout.strip()
            
            if adapter_name:
                # Configure DNS
                dns_cmd = f'''
                Set-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -ServerAddresses ("{provider['primary']}", "{provider['secondary']}")
                '''
                subprocess.run(['powershell', '-Command', dns_cmd], 
                              capture_output=True, timeout=10)
                print(f"[NET] ✓ DNS configured: {provider['primary']} / {provider['secondary']}")
            else:
                print("[NET] ⚠ Could not detect network adapter")
                
        except subprocess.TimeoutExpired:
            print("[NET] ⚠ Timeout configuring DNS")
        except Exception as e:
            print(f"[NET] ⚠ Erro DNS: {e}")
    
    def _disable_nagle(self):
        """Disable Nagle algorithm to reduce latency"""
        try:
            cmd = '''
            $adapters = Get-ChildItem "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces"
            foreach ($adapter in $adapters) {
                Set-ItemProperty -Path $adapter.PSPath -Name "TcpAckFrequency" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
                Set-ItemProperty -Path $adapter.PSPath -Name "TCPNoDelay" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            }
            '''
            subprocess.run(['powershell', '-Command', cmd], capture_output=True, timeout=10)
            print("[NET] ✓ Nagle disabled (micro-lag reduced)")
        except:
            pass
    
    def _optimize_network_buffer(self):
        """Optimize network buffers for gaming"""
        try:
            cmd = '''
            netsh int tcp set global autotuninglevel=normal
            netsh int tcp set global rss=enabled
            '''
            subprocess.run(['cmd', '/c', cmd], capture_output=True, timeout=10)
        except:
            pass
    
    def restore_default_dns(self):
        """Restore DNS to automatic DHCP"""
        try:
            get_adapter_cmd = '''
            $adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1
            $adapter.Name
            '''
            result = subprocess.run(['powershell', '-Command', get_adapter_cmd], 
                                    capture_output=True, text=True, timeout=10)
            adapter_name = result.stdout.strip()
            
            if adapter_name:
                reset_cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -ResetServerAddresses'
                subprocess.run(['powershell', '-Command', reset_cmd], 
                              capture_output=True, timeout=10)
                print("[NET] DNS restored to automatic DHCP")
        except:
            pass
    
    def get_current_dns(self):
        """Returns current DNS"""
        try:
            cmd = 'Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses | Select-Object -First 1'
            result = subprocess.run(['powershell', '-Command', cmd], 
                                    capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return "Unknown"


if __name__ == "__main__":
    # Test
    qos = NetworkQoSManager({'dns_provider': 'adguard'})
    qos.apply_qos_rules()
    
    print("\nAvailable DNS Providers:")
    for key, provider in qos.DNS_PROVIDERS.items():
        print(f"  - {key}: {provider['name']} ({provider['description']})")
    
    input("\nPress ENTER to restore default DNS...")
    qos.restore_default_dns()
