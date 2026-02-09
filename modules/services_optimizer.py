"""
Windows Services Optimizer
Desativa serviços desnecessários para liberar RAM e CPU
"""
import subprocess
import ctypes

class WindowsServicesOptimizer:
    """Otimiza serviços do Windows para gaming/performance"""
    
    # Serviços seguros para desativar (não afetam funcionalidade normal)
    SAFE_TO_DISABLE = {
        # Telemetria / Dados
        'DiagTrack': 'Connected User Experiences and Telemetry',
        'dmwappushservice': 'WAP Push Message Routing Service',
        'diagnosticshub.standardcollector.service': 'Diagnostics Hub',
        
        # Xbox (se não usa Xbox)
        'XblAuthManager': 'Xbox Live Auth Manager',
        'XblGameSave': 'Xbox Live Game Save',
        'XboxGipSvc': 'Xbox Accessory Management',
        'XboxNetApiSvc': 'Xbox Live Networking',
        
        # Outros
        'WSearch': 'Windows Search (indexing)',
        'SysMain': 'Superfetch/SysMain',
        'MapsBroker': 'Downloaded Maps Manager',
        'lfsvc': 'Geolocation Service',
        'RetailDemo': 'Retail Demo Service',
        'WMPNetworkSvc': 'Windows Media Player Network',
    }
    
    # Serviços que PODEM ser desativados (perguntar ao usuário)
    OPTIONAL_DISABLE = {
        'Spooler': 'Print Spooler (desative se não usa impressora)',
        'Fax': 'Fax Service',
        'TabletInputService': 'Touch Keyboard (desative se não usa touch)',
        'WbioSrvc': 'Windows Biometric (desative se não usa fingerprint)',
    }
    
    def __init__(self, config=None):
        self.config = config or {}
        self.disabled_services = []
    
    def is_admin(self):
        """Verifica se tem privilégios de admin"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def get_service_status(self, service_name):
        """Retorna status do serviço"""
        try:
            result = subprocess.run(
                ['sc', 'query', service_name],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            if 'RUNNING' in result.stdout:
                return 'running'
            elif 'STOPPED' in result.stdout:
                return 'stopped'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def disable_service(self, service_name):
        """Desativa um serviço"""
        try:
            # Para o serviço
            subprocess.run(
                ['sc', 'stop', service_name],
                capture_output=True, timeout=10,
                encoding='utf-8', errors='ignore'
            )
            
            # Configura para não iniciar automaticamente
            result = subprocess.run(
                ['sc', 'config', service_name, 'start=', 'disabled'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            
            return result.returncode == 0
        except:
            return False
    
    def enable_service(self, service_name):
        """Reativa um serviço"""
        try:
            subprocess.run(
                ['sc', 'config', service_name, 'start=', 'auto'],
                capture_output=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            subprocess.run(
                ['sc', 'start', service_name],
                capture_output=True, timeout=10,
                encoding='utf-8', errors='ignore'
            )
            return True
        except:
            return False
    
    def optimize(self, aggressive=False):
        """Aplica otimizações de serviços"""
        if not self.is_admin():
            print("[SERVICES] ⚠ Requer privilégios de administrador")
            return False
        
        print("[SERVICES] Otimizando serviços do Windows...")
        
        disabled_count = 0
        ram_saved_estimate = 0
        
        for service, description in self.SAFE_TO_DISABLE.items():
            status = self.get_service_status(service)
            
            if status == 'running':
                if self.disable_service(service):
                    print(f"[SERVICES] ✓ Desativado: {service}")
                    self.disabled_services.append(service)
                    disabled_count += 1
                    ram_saved_estimate += 15  # Estimativa: ~15MB por serviço
            elif status == 'stopped':
                # Já está parado, apenas garante que não inicia
                self.disable_service(service)
        
        print(f"[SERVICES] ✓ {disabled_count} serviços desativados")
        print(f"[SERVICES] ✓ RAM estimada liberada: ~{ram_saved_estimate}MB")
        
        return True
    
    def get_optimization_stats(self):
        """Retorna estatísticas de otimização"""
        return {
            'disabled_count': len(self.disabled_services),
            'disabled_services': self.disabled_services,
            'ram_saved_mb': len(self.disabled_services) * 15
        }
    
    def restore_all(self):
        """Restaura todos os serviços desativados"""
        print("[SERVICES] Restaurando serviços...")
        for service in self.disabled_services:
            self.enable_service(service)
            print(f"[SERVICES] ✓ Restaurado: {service}")
        self.disabled_services = []


if __name__ == "__main__":
    optimizer = WindowsServicesOptimizer()
    
    print("Serviços que serão desativados:")
    for svc, desc in optimizer.SAFE_TO_DISABLE.items():
        status = optimizer.get_service_status(svc)
        print(f"  - {svc}: {desc} [{status}]")
    
    input("\nPressione ENTER para otimizar...")
    optimizer.optimize()
    
    input("\nPressione ENTER para restaurar...")
    optimizer.restore_all()
