using System;
using System.Diagnostics;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Gerenciador de prioridades de processos (similar ao Process Lasso)
    /// </summary>
    public class ProcessPriorityManager
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetPriorityClass(IntPtr hProcess, uint dwPriorityClass);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern int NtSetInformationProcess(IntPtr processHandle, int processInformationClass, ref int processInformation, int processInformationLength);

        // Constantes de prioridade
        private const uint IDLE_PRIORITY_CLASS = 0x0040;
        private const uint BELOW_NORMAL_PRIORITY_CLASS = 0x4000;
        private const uint NORMAL_PRIORITY_CLASS = 0x0020;
        private const uint ABOVE_NORMAL_PRIORITY_CLASS = 0x8000;
        private const uint HIGH_PRIORITY_CLASS = 0x0080;

        // I/O Priority
        private const int ProcessIoPriority = 33;
        private const int IoPriorityVeryLow = 0;
        private const int IoPriorityLow = 1;
        private const int IoPriorityNormal = 2;
        private const int IoPriorityHigh = 3;

        private List<ProcessRule> _rules = new List<ProcessRule>();
        private System.Threading.Timer? _monitorTimer;

        public class ProcessRule
        {
            public string ProcessName { get; set; } = "";
            public ProcessPriorityClass CPUPriority { get; set; } = ProcessPriorityClass.Normal;
            public int IOPriority { get; set; } = IoPriorityNormal;
            public int[]? CPUAffinity { get; set; }
            public bool Enabled { get; set; } = true;
        }

        /// <summary>
        /// Inicia monitoramento de processos
        /// </summary>
        public void Start()
        {
            // Monitora processos a cada 10 segundos
            _monitorTimer = new System.Threading.Timer(
                MonitorProcesses,
                null,
                TimeSpan.Zero,
                TimeSpan.FromSeconds(10)
            );

            Logger.Log("ProcessPriorityManager iniciado", "INFO");
        }

        /// <summary>
        /// Para o monitoramento
        /// </summary>
        public void Stop()
        {
            _monitorTimer?.Dispose();
            Logger.Log("ProcessPriorityManager parado", "INFO");
        }

        /// <summary>
        /// Adiciona uma regra de prioridade
        /// </summary>
        public void AddRule(ProcessRule rule)
        {
            _rules.RemoveAll(r => r.ProcessName.Equals(rule.ProcessName, StringComparison.OrdinalIgnoreCase));
            _rules.Add(rule);
            Logger.Log($"Regra adicionada para: {rule.ProcessName}", "INFO");
        }

        /// <summary>
        /// Remove uma regra
        /// </summary>
        public void RemoveRule(string processName)
        {
            _rules.RemoveAll(r => r.ProcessName.Equals(processName, StringComparison.OrdinalIgnoreCase));
            Logger.Log($"Regra removida para: {processName}", "INFO");
        }

        /// <summary>
        /// Obtém todas as regras
        /// </summary>
        public List<ProcessRule> GetRules() => new List<ProcessRule>(_rules);

        /// <summary>
        /// Monitora e aplica regras aos processos
        /// </summary>
        private void MonitorProcesses(object? state)
        {
            try
            {
                foreach (var rule in _rules.Where(r => r.Enabled))
                {
                    var processes = Process.GetProcessesByName(rule.ProcessName);
                    
                    foreach (var process in processes)
                    {
                        try
                        {
                            ApplyRule(process, rule);
                        }
                        catch (Exception ex)
                        {
                            Logger.Log($"Erro ao aplicar regra em {process.ProcessName}: {ex.Message}", "ERROR");
                        }
                        finally
                        {
                            process.Dispose();
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro no monitoramento de processos: {ex.Message}", "ERROR");
            }
        }

        /// <summary>
        /// Aplica regra a um processo específico
        /// </summary>
        private void ApplyRule(Process process, ProcessRule rule)
        {
            try
            {
                // Aplica prioridade de CPU
                if (process.PriorityClass != rule.CPUPriority)
                {
                    process.PriorityClass = rule.CPUPriority;
                    Logger.Log($"Prioridade CPU aplicada: {process.ProcessName} -> {rule.CPUPriority}", "APPLY");
                }

                // Aplica prioridade de I/O
                SetIOPriority(process.Handle, rule.IOPriority);

                // Aplica afinidade de CPU (se especificado)
                if (rule.CPUAffinity != null && rule.CPUAffinity.Length > 0)
                {
                    long affinity = 0;
                    foreach (var cpu in rule.CPUAffinity)
                    {
                        affinity |= (1L << cpu);
                    }
                    process.ProcessorAffinity = new IntPtr(affinity);
                }
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao aplicar regra: {ex.Message}", "ERROR");
            }
        }

        /// <summary>
        /// Define prioridade de I/O do processo
        /// </summary>
        private void SetIOPriority(IntPtr processHandle, int priority)
        {
            try
            {
                NtSetInformationProcess(processHandle, ProcessIoPriority, ref priority, sizeof(int));
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao definir I/O priority: {ex.Message}", "ERROR");
            }
        }

        /// <summary>
        /// Converte string de prioridade para enum
        /// </summary>
        public static ProcessPriorityClass ParsePriority(string priority)
        {
            return priority.ToLower() switch
            {
                "idle" => ProcessPriorityClass.Idle,
                "belownormal" => ProcessPriorityClass.BelowNormal,
                "normal" => ProcessPriorityClass.Normal,
                "abovenormal" => ProcessPriorityClass.AboveNormal,
                "high" => ProcessPriorityClass.High,
                _ => ProcessPriorityClass.Normal
            };
        }

        /// <summary>
        /// Converte string de I/O priority para valor
        /// </summary>
        public static int ParseIOPriority(string priority)
        {
            return priority.ToLower() switch
            {
                "verylow" => IoPriorityVeryLow,
                "low" => IoPriorityLow,
                "normal" => IoPriorityNormal,
                "high" => IoPriorityHigh,
                _ => IoPriorityNormal
            };
        }
    }
}
