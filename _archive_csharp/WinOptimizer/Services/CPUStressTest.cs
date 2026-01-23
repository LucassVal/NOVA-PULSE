using System;
using System.Threading;
using System.Threading.Tasks;
using System.Diagnostics;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Stress Test controlado de CPU
    /// Mantém CPU em carga constante para estabilidade térmica
    /// </summary>
    public class CPUStressTest
    {
        private CancellationTokenSource? _cancellationTokenSource;
        private Task[]? _workerTasks;
        private bool _isRunning;
        private int _targetLoad; // 0-100%
        private int _threadCount;

        public bool IsRunning => _isRunning;
        public int TargetLoad => _targetLoad;
        public float CurrentCPUUsage { get; private set; }

        private PerformanceCounter? _cpuCounter;

        public event EventHandler<StressTestEventArgs>? StatusChanged;

        public CPUStressTest()
        {
            try
            {
                _cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
                _cpuCounter.NextValue(); // Primeira leitura
            }
            catch
            {
                Logger.Log("Aviso: Contador de CPU não disponível", "WARN");
            }
        }

        /// <summary>
        /// Inicia stress test com carga específica
        /// </summary>
        /// <param name="targetLoadPercentage">Carga desejada (0-100%)</param>
        /// <param name="threadCount">Número de threads (0 = auto = número de cores)</param>
        public void Start(int targetLoadPercentage = 70, int threadCount = 0)
        {
            if (_isRunning)
            {
                Logger.Log("Stress test já está rodando", "WARN");
                return;
            }

            if (targetLoadPercentage < 10 || targetLoadPercentage > 100)
            {
                Logger.Log($"Carga inválida: {targetLoadPercentage}%. Deve estar entre 10-100%", "ERROR");
                return;
            }

            _targetLoad = targetLoadPercentage;
            _threadCount = threadCount <= 0 ? Environment.ProcessorCount : threadCount;

            Logger.Log($"Iniciando stress test: {_targetLoad}% de carga em {_threadCount} threads", "INFO");

            _cancellationTokenSource = new CancellationTokenSource();
            _workerTasks = new Task[_threadCount];

            // Cria worker threads
            for (int i = 0; i < _threadCount; i++)
            {
                int threadId = i;
                _workerTasks[i] = Task.Run(() => WorkerThread(threadId, _cancellationTokenSource.Token));
            }

            // Task de monitoramento
            Task.Run(() => MonitoringThread(_cancellationTokenSource.Token));

            _isRunning = true;
            Logger.Log("Stress test iniciado", "SUCCESS");
        }

        /// <summary>
        /// Para o stress test
        /// </summary>
        public void Stop()
        {
            if (!_isRunning)
            {
                return;
            }

            Logger.Log("Parando stress test...", "INFO");

            _cancellationTokenSource?.Cancel();
            
            try
            {
                Task.WaitAll(_workerTasks ?? Array.Empty<Task>(), TimeSpan.FromSeconds(5));
            }
            catch (AggregateException)
            {
                // Esperado ao cancelar
            }

            _isRunning = false;
            Logger.Log("Stress test parado", "SUCCESS");
        }

        /// <summary>
        /// Thread worker que gera carga na CPU
        /// </summary>
        private void WorkerThread(int threadId, CancellationToken token)
        {
            Logger.Log($"Worker thread {threadId} iniciada", "DEBUG");

            const int checkIntervalMs = 100;
            var stopwatch = new Stopwatch();

            while (!token.IsCancellationRequested)
            {
                stopwatch.Restart();

                // Calcula quanto tempo deve trabalhar vs descansar
                int workTimeMs = (_targetLoad * checkIntervalMs) / 100;
                int sleepTimeMs = checkIntervalMs - workTimeMs;

                // Trabalha (usa CPU)
                if (workTimeMs > 0)
                {
                    var workEnd = stopwatch.ElapsedMilliseconds + workTimeMs;
                    while (stopwatch.ElapsedMilliseconds < workEnd && !token.IsCancellationRequested)
                    {
                        // Operação que usa CPU (cálculo matemático pesado)
                        double dummy = 0;
                        for (int i = 0; i < 1000; i++)
                        {
                            dummy += Math.Sqrt(i) * Math.Sin(i) * Math.Cos(i);
                        }
                    }
                }

                // Descansa (libera CPU)
                if (sleepTimeMs > 0 && !token.IsCancellationRequested)
                {
                    Thread.Sleep(sleepTimeMs);
                }
            }

            Logger.Log($"Worker thread {threadId} finalizada", "DEBUG");
        }

        /// <summary>
        /// Thread de monitoramento do uso real de CPU
        /// </summary>
        private async Task MonitoringThread(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    if (_cpuCounter != null)
                    {
                        CurrentCPUUsage = _cpuCounter.NextValue();
                        
                        StatusChanged?.Invoke(this, new StressTestEventArgs
                        {
                            TargetLoad = _targetLoad,
                            ActualLoad = CurrentCPUUsage,
                            ThreadCount = _threadCount
                        });
                    }

                    await Task.Delay(2000, token);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Logger.Log($"Erro no monitoramento de stress: {ex.Message}", "ERROR");
                }
            }
        }

        /// <summary>
        /// Ajusta a carga durante execução
        /// </summary>
        public void AdjustLoad(int newTargetPercentage)
        {
            if (newTargetPercentage < 10 || newTargetPercentage > 100)
            {
                Logger.Log($"Carga inválida: {newTargetPercentage}%", "ERROR");
                return;
            }

            _targetLoad = newTargetPercentage;
            Logger.Log($"Carga ajustada para {_targetLoad}%", "INFO");
        }

        ~CPUStressTest()
        {
            _cpuCounter?.Dispose();
        }
    }

    public class StressTestEventArgs : EventArgs
    {
        public int TargetLoad { get; set; }
        public float ActualLoad { get; set; }
        public int ThreadCount { get; set; }
    }
}
