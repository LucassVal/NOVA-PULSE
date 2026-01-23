using System;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Serviço de limpeza de memória Standby (cache) similar ao ISLC
    /// </summary>
    public class StandbyMemoryCleaner
    {
        // Importações de APIs nativas do Windows
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool SetProcessWorkingSetSize(IntPtr process, UIntPtr minimumWorkingSetSize, UIntPtr maximumWorkingSetSize);

        [DllImport("psapi.dll", SetLastError = true)]
        private static extern bool EmptyWorkingSet(IntPtr hProcess);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern int NtSetSystemInformation(int SystemInformationClass, ref int SystemInformation, int SystemInformationLength);

        // Constantes para limpeza de memória
        private const int SystemMemoryListInformation = 80;
        private const int MemoryPurgeStandbyList = 4;
        private const int MemoryEmptyWorkingSets = 2;

        private readonly int _thresholdMB;
        private readonly int _checkIntervalSeconds;
        private CancellationTokenSource? _cancellationTokenSource;
        private Task? _monitoringTask;

        public bool IsRunning { get; private set; }
        public long LastCleanedBytes { get; private set; }
        public DateTime LastCleanTime { get; private set; }
        public int CleanCount { get; private set; }

        public event EventHandler<MemoryCleanedEventArgs>? MemoryCleaned;

        public StandbyMemoryCleaner(int thresholdMB = 1024, int checkIntervalSeconds = 5)
        {
            _thresholdMB = thresholdMB;
            _checkIntervalSeconds = checkIntervalSeconds;
        }

        /// <summary>
        /// Inicia o monitoramento e limpeza automática
        /// </summary>
        public void Start()
        {
            if (IsRunning) return;

            _cancellationTokenSource = new CancellationTokenSource();
            _monitoringTask = Task.Run(() => MonitoringLoop(_cancellationTokenSource.Token));
            IsRunning = true;

            Logger.Log("StandbyMemoryCleaner iniciado", "INFO");
        }

        /// <summary>
        /// Para o monitoramento
        /// </summary>
        public void Stop()
        {
            if (!IsRunning) return;

            _cancellationTokenSource?.Cancel();
            _monitoringTask?.Wait(5000);
            IsRunning = false;

            Logger.Log("StandbyMemoryCleaner parado", "INFO");
        }

        /// <summary>
        /// Loop de monitoramento contínuo
        /// </summary>
        private async Task MonitoringLoop(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    var memInfo = GetMemoryInfo();
                    long availableMB = memInfo.AvailableMB;

                    if (availableMB < _thresholdMB)
                    {
                        long freedBytes = CleanStandbyMemory();
                        LastCleanedBytes = freedBytes;
                        LastCleanTime = DateTime.Now;
                        CleanCount++;

                        MemoryCleaned?.Invoke(this, new MemoryCleanedEventArgs
                        {
                            FreedMB = freedBytes / 1024 / 1024,
                            AvailableMB = GetMemoryInfo().AvailableMB,
                            CleanTime = LastCleanTime
                        });

                        Logger.Log($"Memória limpa: {freedBytes / 1024 / 1024} MB liberados", "CLEAN");
                    }

                    await Task.Delay(_checkIntervalSeconds * 1000, token);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Logger.Log($"Erro no monitoramento: {ex.Message}", "ERROR");
                    await Task.Delay(10000, token); // Espera maior em caso de erro
                }
            }
        }

        /// <summary>
        /// Limpa a lista de memória Standby
        /// </summary>
        public long CleanStandbyMemory()
        {
            try
            {
                var memBefore = GetMemoryInfo().AvailableMB;

                // Método 1: Purge Standby List (requer privilégios de administrador)
                int command = MemoryPurgeStandbyList;
                NtSetSystemInformation(SystemMemoryListInformation, ref command, sizeof(int));

                // Método 2: Empty Working Sets (fallback)
                int emptyCommand = MemoryEmptyWorkingSets;
                NtSetSystemInformation(SystemMemoryListInformation, ref emptyCommand, sizeof(int));

                // Aguarda um pouco para o sistema processar
                Thread.Sleep(100);

                var memAfter = GetMemoryInfo().AvailableMB;
                return (memAfter - memBefore) * 1024 * 1024;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao limpar memória: {ex.Message}", "ERROR");
                return 0;
            }
        }

        /// <summary>
        /// Obtém informações atuais da memória
        /// </summary>
        public MemoryInfo GetMemoryInfo()
        {
            var pc = new PerformanceCounter("Memory", "Available MBytes");
            var available = (long)pc.NextValue();

            var totalPhysical = GC.GetGCMemoryInfo().TotalAvailableMemoryBytes / 1024 / 1024;

            return new MemoryInfo
            {
                AvailableMB = available,
                TotalMB = totalPhysical,
                UsedPercentage = totalPhysical > 0 ? (int)((totalPhysical - available) * 100 / totalPhysical) : 0
            };
        }
    }

    public class MemoryInfo
    {
        public long AvailableMB { get; set; }
        public long TotalMB { get; set; }
        public int UsedPercentage { get; set; }
    }

    public class MemoryCleanedEventArgs : EventArgs
    {
        public long FreedMB { get; set; }
        public long AvailableMB { get; set; }
        public DateTime CleanTime { get; set; }
    }

    /// <summary>
    /// Sistema de logging simples
    /// </summary>
    public static class Logger
    {
        private static readonly object _lock = new object();
        private static string LogFile = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "WinOptimizer", "logs.txt");

        public static event EventHandler<LogEventArgs>? LogReceived;

        static Logger()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(LogFile)!);
        }

        public static void Log(string message, string level = "INFO")
        {
            var logEntry = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{level}] {message}";
            
            lock (_lock)
            {
                try
                {
                    File.AppendAllText(LogFile, logEntry + Environment.NewLine);
                }
                catch { }
            }

            LogReceived?.Invoke(null, new LogEventArgs { Message = logEntry, Level = level });
            Console.WriteLine(logEntry);
        }
    }

    public class LogEventArgs : EventArgs
    {
        public string Message { get; set; } = "";
        public string Level { get; set; } = "";
    }
}
