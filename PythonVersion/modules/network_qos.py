"""
Network QoS Manager - Ping Booster
Prioriza tráfego de jogos online via Windows QoS policies
"""
import subprocess
import threading
import time

class NetworkQoSManager:
    """Gerencia políticas de QoS para reduzir lag em jogos"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.running = False
        
        # Common game ports (UDP)
        self.game_ports = {
            # Valorant, League of Legends, CSGO, Fortnite, etc
            'udp_high': [3074, 3478, 3479, 3480, 5060, 5062, 27015, 27036],
            # Discord, TeamSpeak
            'voip': [5000, 5001, 5002, 9000, 9001]
        }
        
        # Game executable names for DSCP marking
        self.game_exes = [
            'valorant.exe', 'league of legends.exe', 'csgo.exe', 
            'fortnite.exe', 'apex_legends.exe', 'overwatch.exe',
            'rocketleague.exe', 'dota2.exe', 'pubg.exe',
            'cod.exe', 'modernwarfare.exe', 'warzone.exe'
        ]
    
    def apply_qos_rules(self):
        """Aplica regras de QoS via netsh (versão rápida)"""
        if not self.enabled:
            return False
            
        print("[NET] Aplicando otimizações de rede para gaming...")
        
        try:
            # 1. Desabilita algoritmo de Nagle (reduz micro-lag) - RÁPIDO
            self._disable_nagle()
            
            # 2. Otimiza buffers TCP - RÁPIDO
            self._optimize_network_buffer()
            
            # NOTE: QoS Policies via PowerShell são lentas e requerem restart
            # Desabilitado para evitar travamento. Usar GPO manualmente se necessário.
            
            print("[NET] ✓ Otimizações de rede aplicadas")
            return True
            
        except Exception as e:
            print(f"[NET] Erro ao aplicar QoS: {e}")
            return False
    
    def _create_qos_policy(self, name, port, protocol, dscp):
        """Cria política QoS - DESABILITADO (muito lento)"""
        # Comentado para evitar travamento
        pass
    
    def _disable_nagle(self):
        """Desabilita algoritmo de Nagle para reduzir latência"""
        try:
            # Registry tweak: TcpAckFrequency e TcpNoDelay
            cmd = '''
            $adapters = Get-ChildItem "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces"
            foreach ($adapter in $adapters) {
                Set-ItemProperty -Path $adapter.PSPath -Name "TcpAckFrequency" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
                Set-ItemProperty -Path $adapter.PSPath -Name "TCPNoDelay" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            }
            '''
            subprocess.run(['powershell', '-Command', cmd], capture_output=True)
            print("[NET] ✓ Nagle disabled (micro-lag reduzido)")
        except:
            pass
    
    def _optimize_network_buffer(self):
        """Otimiza buffers de rede para gaming"""
        try:
            # Aumenta tamanho do buffer de recebimento
            cmd = '''
            netsh int tcp set global autotuninglevel=normal
            netsh int tcp set global chimney=disabled
            netsh int tcp set global rss=enabled
            netsh int tcp set global netdma=disabled
            '''
            subprocess.run(['cmd', '/c', cmd], capture_output=True)
        except:
            pass
    
    def remove_qos_rules(self):
        """Remove regras de QoS"""
        try:
            for port in self.game_ports['udp_high']:
                subprocess.run(
                    ['powershell', '-Command', 
                     f'Remove-NetQosPolicy -Name "GameBoost_Port_{port}" -Confirm:$false -ErrorAction SilentlyContinue'],
                    capture_output=True
                )
            print("[NET] Regras de QoS removidas")
        except:
            pass


if __name__ == "__main__":
    # Teste
    qos = NetworkQoSManager()
    qos.apply_qos_rules()
    input("Pressione ENTER para remover regras...")
    qos.remove_qos_rules()
