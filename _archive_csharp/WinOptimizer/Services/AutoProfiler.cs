using System;
using System.Diagnostics;
using System.Threading;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Sistema de modos do NovaPulse
    /// </summary>
    public enum SystemMode
    {
        Boost,   // Máxima performance (CPU > 85%)
        Normal,  // Operação padrão
        Eco      // Economia de energia (CPU < 30%)
    }
    
    /// <summary>
    /// Auto-Profiler para detecção automática de carga do sistema.
    /// Ajusta CPU e RAM baseado na carga real em tempo real.
    /// </summary>
    public class AutoProfiler
    {
        private readonly CPUPowerManager? _cpuManager;
        private readonly StandbyMemoryCleaner? _memoryCleaner;
        private Thread? _monitorThread;
        private bool _running;
        
        // Configuration
        public int CheckIntervalMs { get; set; } = 2000;  // 2 seconds
        public int BoostThreshold { get; set; } = 85;     // CPU > 85%
        public int EcoThreshold { get; set; } = 30;       // CPU < 30%
        public int BoostHoldTime { get; set; } = 2;       // Seconds to activate boost
        public int EcoHoldTime { get; set; } = 5;         // Seconds to activate eco
        
        // State
        public SystemMode CurrentMode { get; private set; } = SystemMode.Normal;
        private SystemMode _previousMode = SystemMode.Normal;
        
        // CPU Usage tracking
        private readonly PerformanceCounter _cpuCounter;
        private float[] _cpuHistory = new float[10];
        private int _historyIndex = 0;
        
        // Counters
        private int _highCpuCounter = 0;
        private int _lowCpuCounter = 0;
        
        // Events
        public event EventHandler<SystemMode>? ModeChanged;
        
        public AutoProfiler(CPUPowerManager? cpuManager = null, StandbyMemoryCleaner? memoryCleaner = null)
        {
            _cpuManager = cpuManager;
            _memoryCleaner = memoryCleaner;
            
            // Initialize CPU counter
            _cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
            _cpuCounter.NextValue(); // First call always returns 0
        }
        
        public void Start()
        {
            if (_running) return;
            
            _running = true;
            _monitorThread = new Thread(MonitoringLoop)
            {
                IsBackground = true,
                Name = "NovaPulse-AutoProfiler"
            };
            _monitorThread.Start();
            
            Logger.Log($"[AUTO] NovaPulse Auto-Profiler started", "INFO");
            Logger.Log($"[AUTO] → BOOST: CPU > {BoostThreshold}%", "INFO");
            Logger.Log($"[AUTO] → ECO: CPU < {EcoThreshold}%", "INFO");
        }
        
        public void Stop()
        {
            _running = false;
            _monitorThread?.Join(5000);
            Logger.Log("[AUTO] Auto-Profiler stopped", "INFO");
        }
        
        private void MonitoringLoop()
        {
            while (_running)
            {
                try
                {
                    // Get CPU usage
                    float cpuPercent = _cpuCounter.NextValue();
                    
                    // Add to history
                    _cpuHistory[_historyIndex] = cpuPercent;
                    _historyIndex = (_historyIndex + 1) % _cpuHistory.Length;
                    
                    // Calculate average
                    float avgCpu = GetAverageCpu();
                    
                    // Determine mode
                    var newMode = DetermineMode(avgCpu);
                    
                    // Apply if changed
                    if (newMode != CurrentMode)
                    {
                        ApplyMode(newMode);
                    }
                    
                    Thread.Sleep(CheckIntervalMs);
                }
                catch (Exception ex)
                {
                    Logger.Log($"[AUTO] Error: {ex.Message}", "ERROR");
                    Thread.Sleep(5000);
                }
            }
        }
        
        public float GetAverageCpu()
        {
            float sum = 0;
            int count = 0;
            foreach (var val in _cpuHistory)
            {
                if (val > 0)
                {
                    sum += val;
                    count++;
                }
            }
            return count > 0 ? sum / count : 0;
        }
        
        private SystemMode DetermineMode(float avgCpu)
        {
            // Check for BOOST
            if (avgCpu > BoostThreshold)
            {
                _highCpuCounter++;
                _lowCpuCounter = 0;
                
                if (_highCpuCounter >= (BoostHoldTime * 1000 / CheckIntervalMs))
                {
                    return SystemMode.Boost;
                }
            }
            // Check for ECO
            else if (avgCpu < EcoThreshold)
            {
                _lowCpuCounter++;
                _highCpuCounter = 0;
                
                if (_lowCpuCounter >= (EcoHoldTime * 1000 / CheckIntervalMs))
                {
                    return SystemMode.Eco;
                }
            }
            // Reset to NORMAL
            else
            {
                _highCpuCounter = 0;
                _lowCpuCounter = 0;
                
                if (CurrentMode != SystemMode.Normal)
                {
                    return SystemMode.Normal;
                }
            }
            
            return CurrentMode;
        }
        
        private void ApplyMode(SystemMode newMode)
        {
            _previousMode = CurrentMode;
            CurrentMode = newMode;
            
            Logger.Log($"[AUTO] Mode Change: {_previousMode} → {newMode}", "INFO");
            
            switch (newMode)
            {
                case SystemMode.Boost:
                    ApplyBoostMode();
                    break;
                case SystemMode.Eco:
                    ApplyEcoMode();
                    break;
                default:
                    ApplyNormalMode();
                    break;
            }
            
            ModeChanged?.Invoke(this, newMode);
        }
        
        private void ApplyBoostMode()
        {
            Logger.Log("[AUTO] ⚡ BOOST MODE - Maximum Performance!", "SUCCESS");
            
            _cpuManager?.SetMaxCpuFrequency(100);
            
            if (_memoryCleaner != null)
            {
                _memoryCleaner.ThresholdMB = 2048;
                _memoryCleaner.CheckIntervalSeconds = 2;
                _memoryCleaner.CleanStandbyMemory(); // Force clean
            }
        }
        
        private void ApplyEcoMode()
        {
            Logger.Log("[AUTO] 🌿 ECO MODE - Power Saving", "INFO");
            
            _cpuManager?.SetMaxCpuFrequency(70);
            
            if (_memoryCleaner != null)
            {
                _memoryCleaner.ThresholdMB = 8192;
                _memoryCleaner.CheckIntervalSeconds = 30;
            }
        }
        
        private void ApplyNormalMode()
        {
            Logger.Log("[AUTO] 🔄 NORMAL MODE - Balanced", "INFO");
            
            _cpuManager?.SetMaxCpuFrequency(85);
            
            if (_memoryCleaner != null)
            {
                _memoryCleaner.ThresholdMB = 4096;
                _memoryCleaner.CheckIntervalSeconds = 5;
            }
        }
        
        public void ForceMode(SystemMode mode)
        {
            Logger.Log($"[AUTO] Manual override: {mode}", "INFO");
            ApplyMode(mode);
            _highCpuCounter = 0;
            _lowCpuCounter = 0;
        }
        
        public string GetModeDisplayName()
        {
            return CurrentMode switch
            {
                SystemMode.Boost => "⚡ BOOST",
                SystemMode.Eco => "🌿 ECO",
                _ => "🔄 NORMAL"
            };
        }
    }
}
