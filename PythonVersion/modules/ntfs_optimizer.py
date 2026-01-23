"""
NovaPulse - NTFS Optimizer
Otimizações de sistema de arquivos NTFS para melhor I/O
"""
import subprocess
import ctypes
import winreg
from typing import Dict, Tuple


class NTFSOptimizer:
    """Otimiza configurações do sistema de arquivos NTFS"""
    
    def __init__(self):
        self.applied_changes = {}
        self.is_admin = self._check_admin()
    
    def _check_admin(self) -> bool:
        """Verifica privilégios de admin"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_fsutil(self, args: str) -> Tuple[bool, str]:
        """Executa comando fsutil"""
        try:
            result = subprocess.run(
                f"fsutil behavior set {args}",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def disable_8dot3_names(self) -> bool:
        """
        Desativa criação de nomes curtos 8.3 (legado DOS)
        Impacto: Melhora performance de criação de arquivos
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("disable8dot3 1")
        self.applied_changes['8dot3'] = success
        
        if success:
            print("[NTFS] ✓ 8.3 filenames desativados")
        else:
            print(f"[NTFS] ✗ Erro ao desativar 8.3: {output}")
        
        return success
    
    def disable_last_access_time(self) -> bool:
        """
        Desativa atualização de Last Access Time
        Impacto: Reduz writes desnecessários (especialmente em SSDs)
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("disablelastaccess 1")
        self.applied_changes['lastaccess'] = success
        
        if success:
            print("[NTFS] ✓ Last Access Time desativado")
        else:
            print(f"[NTFS] ✗ Erro ao desativar Last Access: {output}")
        
        return success
    
    def optimize_memory_usage(self, large_cache: bool = False) -> bool:
        """
        Otimiza uso de memória para cache de arquivos
        large_cache=True: Prioriza cache (bom para servidores)
        large_cache=False: Prioriza aplicativos (bom para desktop/gaming)
        """
        if not self.is_admin:
            return False
        
        value = 1 if large_cache else 0
        success, output = self._run_fsutil(f"memoryusage {value}")
        self.applied_changes['memoryusage'] = success
        
        if success:
            mode = "cache" if large_cache else "apps"
            print(f"[NTFS] ✓ Memória otimizada para {mode}")
        
        return success
    
    def disable_encryption(self) -> bool:
        """
        Desativa EFS (Encrypting File System) no sistema
        Impacto: Pequena melhoria em I/O
        """
        if not self.is_admin:
            return False
        
        success, output = self._run_fsutil("encryptpagingfile 0")
        self.applied_changes['encryption'] = success
        
        if success:
            print("[NTFS] ✓ Encryption pagefile desativado")
        
        return success
    
    def set_mft_zone(self, size: int = 2) -> bool:
        """
        Define tamanho da MFT Zone (1-4)
        1 = 12.5%, 2 = 25%, 3 = 37.5%, 4 = 50%
        Maior = menos fragmentação para muitos arquivos pequenos
        """
        if not self.is_admin:
            return False
        
        size = max(1, min(4, size))
        success, output = self._run_fsutil(f"mftzone {size}")
        self.applied_changes['mftzone'] = success
        
        if success:
            print(f"[NTFS] ✓ MFT Zone definido para {size}")
        
        return success
    
    def apply_all_optimizations(self, gaming_mode: bool = True) -> Dict[str, bool]:
        """
        Aplica todas as otimizações NTFS
        gaming_mode=True: Prioriza aplicativos sobre cache
        """
        print("\n[NTFS] Aplicando otimizações do sistema de arquivos...")
        
        results = {}
        results['8dot3'] = self.disable_8dot3_names()
        results['lastaccess'] = self.disable_last_access_time()
        results['memoryusage'] = self.optimize_memory_usage(large_cache=not gaming_mode)
        results['encryption'] = self.disable_encryption()
        results['mftzone'] = self.set_mft_zone(2)
        
        success_count = sum(results.values())
        print(f"[NTFS] Resultado: {success_count}/{len(results)} otimizações aplicadas")
        
        return results
    
    def get_status(self) -> Dict[str, str]:
        """Retorna status atual das configurações NTFS"""
        status = {}
        
        try:
            # Query current settings
            result = subprocess.run(
                "fsutil behavior query disable8dot3",
                shell=True, capture_output=True, text=True
            )
            status['8dot3'] = "Desativado" if "1" in result.stdout else "Ativado"
            
            result = subprocess.run(
                "fsutil behavior query disablelastaccess",
                shell=True, capture_output=True, text=True
            )
            status['lastaccess'] = "Desativado" if "1" in result.stdout or "2" in result.stdout else "Ativado"
            
        except:
            pass
        
        return status


# Singleton
_instance = None

def get_optimizer() -> NTFSOptimizer:
    global _instance
    if _instance is None:
        _instance = NTFSOptimizer()
    return _instance


if __name__ == "__main__":
    optimizer = NTFSOptimizer()
    print("Status atual:", optimizer.get_status())
    # optimizer.apply_all_optimizations()
