"""
History Logger - CSV Log de Limpezas
Salva histórico de todas as operações de limpeza
"""
import csv
import os
from datetime import datetime
from pathlib import Path

class HistoryLogger:
    """Gerencia histórico de limpezas em CSV"""
    
    def __init__(self, log_dir=None):
        # Diretório de logs
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".nvme_optimizer" / "logs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_log = self.log_dir / "cleanup_history.csv"
        self.events_log = self.log_dir / "events.csv"
        
        # Inicializa arquivos se não existirem
        self._init_files()
    
    def _init_files(self):
        """Cria arquivos CSV com headers se não existirem"""
        if not self.cleanup_log.exists():
            with open(self.cleanup_log, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'freed_mb', 'trigger', 'ram_before_mb', 'ram_after_mb'])
        
        if not self.events_log.exists():
            with open(self.events_log, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'event_type', 'details'])
    
    def log_cleanup(self, freed_mb: float, trigger: str = "auto", 
                    ram_before_mb: float = 0, ram_after_mb: float = 0):
        """Registra uma limpeza de memória"""
        timestamp = datetime.now().isoformat()
        
        try:
            with open(self.cleanup_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, freed_mb, trigger, ram_before_mb, ram_after_mb])
        except Exception as e:
            print(f"[HISTORY] Erro ao salvar log: {e}")
    
    def log_event(self, event_type: str, details: str = ""):
        """Registra um evento genérico"""
        timestamp = datetime.now().isoformat()
        
        try:
            with open(self.events_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, event_type, details])
        except:
            pass
    
    def get_cleanup_stats(self) -> dict:
        """Retorna estatísticas de limpezas"""
        stats = {
            'total_cleanups': 0,
            'total_freed_mb': 0,
            'avg_freed_mb': 0,
            'last_cleanup': None
        }
        
        try:
            with open(self.cleanup_log, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if rows:
                    stats['total_cleanups'] = len(rows)
                    stats['total_freed_mb'] = sum(float(r['freed_mb']) for r in rows)
                    stats['avg_freed_mb'] = stats['total_freed_mb'] / stats['total_cleanups']
                    stats['last_cleanup'] = rows[-1]['timestamp']
        except:
            pass
        
        return stats
    
    def get_log_path(self) -> Path:
        """Retorna caminho da pasta de logs"""
        return self.log_dir


# Singleton global
_instance = None

def get_logger() -> HistoryLogger:
    """Retorna instância singleton do logger"""
    global _instance
    if _instance is None:
        _instance = HistoryLogger()
    return _instance


if __name__ == "__main__":
    # Teste
    logger = get_logger()
    
    # Simula algumas limpezas
    logger.log_cleanup(512, "auto", 4096, 4608)
    logger.log_cleanup(256, "manual", 3500, 3756)
    logger.log_event("game_start", "valorant.exe")
    
    print(f"Logs salvos em: {logger.get_log_path()}")
    print(f"Estatísticas: {logger.get_cleanup_stats()}")
