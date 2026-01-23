using System;
using System.Diagnostics;
using System.IO;
using Microsoft.Win32.TaskScheduler;

namespace WinOptimizer.Installer
{
    /// <summary>
    /// Configura auto-start do WinOptimizer via Task Scheduler
    /// </summary>
    public static class AutoStartSetup
    {
        private const string TaskName = "WinOptimizerAutoStart";
        private const string TaskDescription = "Inicia automaticamente o Windows NVMe RAM Optimizer com privilégios elevados";

        /// <summary>
        /// Instala task no Task Scheduler para auto-start
        /// </summary>
        public static bool InstallAutoStart()
        {
            try
            {
                // Caminho do executável
                string exePath = Process.GetCurrentProcess().MainModule?.FileName ?? "";
                
                if (string.IsNullOrEmpty(exePath))
                {
                    Logger.Log("Erro: não foi possível determinar caminho do executável", "ERROR");
                    return false;
                }

                Logger.Log("Instalando auto-start...", "INFO");

                using (TaskService ts = new TaskService())
                {
                    // Remove task existente se houver
                    ts.RootFolder.DeleteTask(TaskName, false);

                    // Cria nova task definition
                    TaskDefinition td = ts.NewTask();
                    td.RegistrationInfo.Description = TaskDescription;
                    td.RegistrationInfo.Author = "Windows Optimizer";

                    // Trigger: ao iniciar o sistema (com delay de 30s)
                    td.Triggers.Add(new BootTrigger { Delay = TimeSpan.FromSeconds(30) });

                    // Action: executar o programa
                    td.Actions.Add(new ExecAction(exePath));

                    // Settings
                    td.Principal.RunLevel = TaskRunLevel.Highest; // Roda como admin
                    td.Settings.DisallowStartIfOnBatteries = false;
                    td.Settings.StopIfGoingOnBatteries = false;
                    td.Settings.ExecutionTimeLimit = TimeSpan.Zero; // Sem limite de tempo
                    td.Settings.Priority = ProcessPriorityClass.Normal;

                    // Registra a task
                    ts.RootFolder.RegisterTaskDefinition(TaskName, td);
                }

                Logger.Log("✓ Auto-start instalado com sucesso", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao instalar auto-start: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Desinstala o auto-start
        /// </summary>
        public static bool UninstallAutoStart()
        {
            try
            {
                Logger.Log("Removendo auto-start...", "INFO");

                using (TaskService ts = new TaskService())
                {
                    ts.RootFolder.DeleteTask(TaskName, false);
                }

                Logger.Log("✓ Auto-start removido", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao remover auto-start: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Verifica se auto-start está instalado
        /// </summary>
        public static bool IsAutoStartInstalled()
        {
            try
            {
                using (TaskService ts = new TaskService())
                {
                    var task = ts.GetTask(TaskName);
                    return task != null;
                }
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Instala através de PowerShell (fallback se TaskService não funcionar)
        /// </summary>
        public static bool InstallViaPowerShell()
        {
            try
            {
                string exePath = Process.GetCurrentProcess().MainModule?.FileName ?? "";
                
                string psScript = $@"
$Action = New-ScheduledTaskAction -Execute '{exePath}'
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest
Register-ScheduledTask -TaskName '{TaskName}' -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
";

                var psi = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = $"-NoProfile -ExecutionPolicy Bypass -Command \"{psScript}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                using var process = Process.Start(psi);
                process?.WaitForExit();

                return process?.ExitCode == 0;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao instalar via PowerShell: {ex.Message}", "ERROR");
                return false;
            }
        }
    }
}
