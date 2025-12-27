"""
Profile System - Perfis de Otimização
Permite alternar entre diferentes modos de otimização
"""
import yaml
from pathlib import Path
from enum import Enum

class OptimizationProfile(Enum):
    GAMING = "gaming"
    PRODUCTIVITY = "productivity"
    BATTERY_SAVER = "battery_saver"
    BALANCED = "balanced"

class ProfileManager:
    """Gerencia perfis de otimização"""
    
    # Configurações padrão para cada perfil
    PROFILES = {
        OptimizationProfile.GAMING: {
            'name': '🎮 Gaming',
            'description': 'Máxima performance para jogos',
            'cpu_max_freq': 100,
            'cpu_min_freq': 50,
            'ram_threshold_mb': 2048,  # Limpa RAM mais agressivamente
            'ram_check_interval': 3,
            'network_qos': True,
            'game_boost': True,
            'thermal_limit': 90  # Permite mais calor
        },
        OptimizationProfile.PRODUCTIVITY: {
            'name': '💼 Produtividade',
            'description': 'Balanceado para trabalho',
            'cpu_max_freq': 95,
            'cpu_min_freq': 20,
            'ram_threshold_mb': 4096,
            'ram_check_interval': 10,
            'network_qos': False,
            'game_boost': False,
            'thermal_limit': 80
        },
        OptimizationProfile.BATTERY_SAVER: {
            'name': '🔋 Economia',
            'description': 'Máxima economia de bateria',
            'cpu_max_freq': 70,
            'cpu_min_freq': 5,
            'ram_threshold_mb': 8192,  # Só limpa quando realmente necessário
            'ram_check_interval': 30,
            'network_qos': False,
            'game_boost': False,
            'thermal_limit': 70
        },
        OptimizationProfile.BALANCED: {
            'name': '⚖️ Balanceado',
            'description': 'Equilíbrio entre performance e consumo',
            'cpu_max_freq': 85,
            'cpu_min_freq': 10,
            'ram_threshold_mb': 4096,
            'ram_check_interval': 5,
            'network_qos': True,
            'game_boost': True,
            'thermal_limit': 80
        }
    }
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or 'config.yaml'
        self.current_profile = OptimizationProfile.BALANCED
        self.services = {}
    
    def set_services(self, services: dict):
        """Define referência aos serviços do otimizador"""
        self.services = services
    
    def get_current_profile(self) -> OptimizationProfile:
        """Retorna perfil atual"""
        return self.current_profile
    
    def get_profile_settings(self, profile: OptimizationProfile = None) -> dict:
        """Retorna configurações do perfil"""
        if profile is None:
            profile = self.current_profile
        return self.PROFILES.get(profile, self.PROFILES[OptimizationProfile.BALANCED])
    
    def apply_profile(self, profile: OptimizationProfile):
        """Aplica um perfil de otimização"""
        if profile not in self.PROFILES:
            print(f"[PROFILE] Perfil inválido: {profile}")
            return False
        
        settings = self.PROFILES[profile]
        self.current_profile = profile
        
        print(f"[PROFILE] Aplicando perfil: {settings['name']}")
        print(f"[PROFILE] {settings['description']}")
        
        try:
            # Aplica configurações de CPU
            if 'cpu_power' in self.services:
                cpu = self.services['cpu_power']
                cpu.set_max_cpu_frequency(settings['cpu_max_freq'])
                cpu.set_min_cpu_frequency(settings['cpu_min_freq'])
            
            # Aplica configurações de RAM
            if 'cleaner' in self.services:
                cleaner = self.services['cleaner']
                cleaner.threshold_mb = settings['ram_threshold_mb']
                cleaner.check_interval = settings['ram_check_interval']
            
            print(f"[PROFILE] ✓ Perfil {settings['name']} aplicado!")
            return True
            
        except Exception as e:
            print(f"[PROFILE] Erro ao aplicar perfil: {e}")
            return False
    
    def list_profiles(self) -> list:
        """Lista todos os perfis disponíveis"""
        profiles = []
        for profile, settings in self.PROFILES.items():
            profiles.append({
                'id': profile.value,
                'name': settings['name'],
                'description': settings['description']
            })
        return profiles


# Singleton global
_instance = None

def get_manager() -> ProfileManager:
    """Retorna instância singleton"""
    global _instance
    if _instance is None:
        _instance = ProfileManager()
    return _instance


if __name__ == "__main__":
    # Teste
    manager = get_manager()
    
    print("Perfis disponíveis:")
    for p in manager.list_profiles():
        print(f"  - {p['name']}: {p['description']}")
    
    print("\nConfigurações do perfil Gaming:")
    print(manager.get_profile_settings(OptimizationProfile.GAMING))
