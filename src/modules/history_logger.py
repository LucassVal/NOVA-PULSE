"""
History Logger - CSV Cleanup Log
Saves history of all cleanup operations
"""
import csv
import os
from datetime import datetime
from pathlib import Path

class HistoryLogger:
    """Manages cleanup history in CSV"""
    
    def __init__(self, log_dir=None):
        # Log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".nvme_optimizer" / "logs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cleanup_log = self.log_dir / "cleanup_history.csv"
        self.events_log = self.log_dir / "events.csv"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Create CSV files with headers if they don't exist"""
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
        """Record a memory cleanup"""
        timestamp = datetime.now().isoformat()
        
        try:
            with open(self.cleanup_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, freed_mb, trigger, ram_before_mb, ram_after_mb])
        except Exception as e:
            print(f"[HISTORY] Error saving log: {e}")
    
    def log_event(self, event_type: str, details: str = ""):
        """Record a generic event"""
        timestamp = datetime.now().isoformat()
        
        try:
            with open(self.events_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, event_type, details])
        except:
            pass
    
    def get_cleanup_stats(self) -> dict:
        """Returns cleanup statistics"""
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
        """Returns the log folder path"""
        return self.log_dir


# Global singleton
_instance = None

def get_logger() -> HistoryLogger:
    """Returns singleton logger instance"""
    global _instance
    if _instance is None:
        _instance = HistoryLogger()
    return _instance


if __name__ == "__main__":
    # Test
    logger = get_logger()
    
    # Simulate some cleanups
    logger.log_cleanup(512, "auto", 4096, 4608)
    logger.log_cleanup(256, "manual", 3500, 3756)
    logger.log_event("game_start", "valorant.exe")
    
    print(f"Logs saved to: {logger.get_log_path()}")
    print(f"Statistics: {logger.get_cleanup_stats()}")
