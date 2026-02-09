"""
Windows Services Optimizer
Disables unnecessary services to free RAM and CPU
"""
import subprocess
import ctypes

class WindowsServicesOptimizer:
    """Optimizes Windows services for gaming/performance"""
    
    # Services safe to disable (don't affect normal functionality)
    SAFE_TO_DISABLE = {
        # Telemetry / Data
        'DiagTrack': 'Connected User Experiences and Telemetry',
        'dmwappushservice': 'WAP Push Message Routing Service',
        'diagnosticshub.standardcollector.service': 'Diagnostics Hub',
        
        # Xbox (if not using Xbox)
        'XblAuthManager': 'Xbox Live Auth Manager',
        'XblGameSave': 'Xbox Live Game Save',
        'XboxGipSvc': 'Xbox Accessory Management',
        'XboxNetApiSvc': 'Xbox Live Networking',
        
        # Other
        'WSearch': 'Windows Search (indexing)',
        'SysMain': 'Superfetch/SysMain',
        'MapsBroker': 'Downloaded Maps Manager',
        'lfsvc': 'Geolocation Service',
        'RetailDemo': 'Retail Demo Service',
        'WMPNetworkSvc': 'Windows Media Player Network',
    }
    
    # Services that CAN be disabled (ask user)
    OPTIONAL_DISABLE = {
        'Spooler': 'Print Spooler (disable if not using a printer)',
        'Fax': 'Fax Service',
        'TabletInputService': 'Touch Keyboard (disable if not using touch)',
        'WbioSrvc': 'Windows Biometric (disable if not using fingerprint)',
    }
    
    def __init__(self, config=None):
        self.config = config or {}
        self.disabled_services = []
    
    def is_admin(self):
        """Check for admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def get_service_status(self, service_name):
        """Returns service status"""
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
        """Disable a service"""
        try:
            # Stop the service
            subprocess.run(
                ['sc', 'stop', service_name],
                capture_output=True, timeout=10,
                encoding='utf-8', errors='ignore'
            )
            
            # Configure not to start automatically
            result = subprocess.run(
                ['sc', 'config', service_name, 'start=', 'disabled'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            
            return result.returncode == 0
        except:
            return False
    
    def enable_service(self, service_name):
        """Re-enable a service"""
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
        """Apply service optimizations"""
        if not self.is_admin():
            print("[SERVICES] ⚠ Requires administrator privileges")
            return False
        
        print("[SERVICES] Optimizing Windows services...")
        
        disabled_count = 0
        ram_saved_estimate = 0
        
        for service, description in self.SAFE_TO_DISABLE.items():
            status = self.get_service_status(service)
            
            if status == 'running':
                if self.disable_service(service):
                    print(f"[SERVICES] ✓ Disabled: {service}")
                    self.disabled_services.append(service)
                    disabled_count += 1
                    ram_saved_estimate += 15  # Estimate: ~15MB per service
            elif status == 'stopped':
                # Already stopped, just ensure it doesn't start
                self.disable_service(service)
        
        print(f"[SERVICES] ✓ {disabled_count} services disabled")
        print(f"[SERVICES] ✓ Estimated RAM freed: ~{ram_saved_estimate}MB")
        
        return True
    
    def get_optimization_stats(self):
        """Returns optimization statistics"""
        return {
            'disabled_count': len(self.disabled_services),
            'disabled_services': self.disabled_services,
            'ram_saved_mb': len(self.disabled_services) * 15
        }
    
    def restore_all(self):
        """Restore all disabled services"""
        print("[SERVICES] Restoring services...")
        for service in self.disabled_services:
            self.enable_service(service)
            print(f"[SERVICES] ✓ Restored: {service}")
        self.disabled_services = []


if __name__ == "__main__":
    optimizer = WindowsServicesOptimizer()
    
    print("Services that will be disabled:")
    for svc, desc in optimizer.SAFE_TO_DISABLE.items():
        status = optimizer.get_service_status(svc)
        print(f"  - {svc}: {desc} [{status}]")
    
    input("\nPress ENTER to optimize...")
    optimizer.optimize()
    
    input("\nPress ENTER to restore...")
    optimizer.restore_all()
