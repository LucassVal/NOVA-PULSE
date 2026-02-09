"""
Game Mode Detector
Detecta quando um jogo está rodando e aplica otimizações extras
"""
import psutil
import threading
import time

class GameModeDetector:
    """Detecta jogos e aplica otimizações automáticas"""
    
    def __init__(self, optimizer_services=None, config=None):
        self.config = config or {}
        self.services = optimizer_services or {}
        self.running = False
        self.thread = None
        self.game_active = False
        self.current_game = None
        
        # Lista de executáveis de jogos conhecidos
        self.known_games = {
            # FPS
            'valorant.exe', 'valorant-win64-shipping.exe',
            'csgo.exe', 'cs2.exe',
            'overwatch.exe',
            'apex_legends.exe', 'r5apex.exe',
            'fortnite.exe', 'fortniteclient-win64-shipping.exe',
            'cod.exe', 'modernwarfare.exe', 'blackopscoldwar.exe',
            'pubg.exe', 'tslgame.exe',
            'rainbowsix.exe', 'rainbow6.exe',
            'destiny2.exe',
            'tarkov.exe', 'escapefromtarkov.exe',
            'battlefield.exe', 'bf2042.exe',
            
            # MOBA/Strategy
            'league of legends.exe', 'leagueclient.exe',
            'dota2.exe',
            'rocketleague.exe',
            
            # Racing
            'forzahorizon5.exe', 'forzahorizon4.exe',
            'assettocorsa.exe',
            
            # RPG/Open World
            'gta5.exe', 'gtav.exe', 'playgtav.exe',
            'cyberpunk2077.exe',
            'eldenring.exe',
            'hogwartslegacy.exe',
            
            # Minecraft/Sandbox
            'javaw.exe',  # Minecraft Java
            'minecraft.windows.exe',
            
            # Emulators
            'rpcs3.exe', 'yuzu.exe', 'ryujinx.exe',
            
            # VR
            'vrserver.exe', 'vrclient.exe'
        }
        
        # Processos adicionais do config
        extra_games = self.config.get('extra_game_exes', [])
        for game in extra_games:
            self.known_games.add(game.lower())
    
    def start(self):
        """Inicia monitoramento de jogos"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        print("[GAME] Detector de jogos iniciado")
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _detection_loop(self):
        """Loop de detecção de jogos"""
        while self.running:
            try:
                game_found = None
                
                # Verifica processos ativos
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        name = proc.info['name'].lower()
                        if name in self.known_games:
                            game_found = name
                            break
                    except:
                        continue
                
                # Estado mudou?
                if game_found and not self.game_active:
                    self._on_game_start(game_found)
                elif not game_found and self.game_active:
                    self._on_game_end()
                
                time.sleep(5)  # Verifica a cada 5 segundos
                
            except Exception as e:
                time.sleep(10)
    
    def _on_game_start(self, game_name):
        """Chamado quando um jogo é detectado"""
        self.game_active = True
        self.current_game = game_name
        print(f"[GAME] 🎮 Jogo detectado: {game_name.upper()}")
        print("[GAME] Aplicando otimizações de gaming...")
        
        # Aplica boost
        self._apply_game_boost()
    
    def _on_game_end(self):
        """Chamado quando o jogo fecha"""
        old_game = self.current_game
        self.game_active = False
        self.current_game = None
        print(f"[GAME] 🛑 Jogo encerrado: {old_game}")
        print("[GAME] Restaurando configurações normais...")
        
        # Restaura configurações
        self._restore_normal()
    
    def _apply_game_boost(self):
        """Aplica otimizações para gaming.
        
        Note: CPU frequency is NOT overridden to 100% here.
        The auto_profiler's 80% cap already allows Intel Turbo Boost 3.0
        to spike single-core to 4.4GHz for burst workloads.
        Removing the 100% override prevents thermal throttling.
        """
        try:
            # 1. Força limpeza de RAM para liberar memória ao jogo
            if 'cleaner' in self.services:
                self.services['cleaner'].clean_standby_memory()
            
            # 2. Aumenta prioridade do jogo (handled by SmartProcessManager)
            
            print("[GAME] ⚡ GAME MODE ATIVADO - Performance máxima!")
            
        except Exception as e:
            print(f"[GAME] Erro ao aplicar boost: {e}")
    
    def _restore_normal(self):
        """Restaura configurações normais"""
        try:
            # CPU volta ao gerenciamento automático
            # (o Thermal Governor vai cuidar)
            print("[GAME] Configurações normais restauradas")
        except:
            pass
    
    def is_game_active(self) -> bool:
        """Retorna se um jogo está ativo"""
        return self.game_active
    
    def get_current_game(self) -> str:
        """Retorna nome do jogo atual"""
        return self.current_game


if __name__ == "__main__":
    # Teste
    detector = GameModeDetector()
    detector.start()
    
    print("Monitorando jogos... Pressione Ctrl+C para parar")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.stop()
        print("Finalizado")
