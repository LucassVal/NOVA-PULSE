using System;
using System.ServiceProcess;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Controlador de serviços do Windows (SysMain/Superfetch)
    /// </summary>
    public class SystemServiceController
    {
        private const string SysMainServiceName = "SysMain";

        /// <summary>
        /// Obtém status do serviço SysMain
        /// </summary>
        public ServiceControllerStatus GetSysMainStatus()
        {
            try
            {
                using var service = new ServiceController(SysMainServiceName);
                return service.Status;
            }
            catch
            {
                return ServiceControllerStatus.Stopped;
            }
        }

        /// <summary>
        /// Para o serviço SysMain
        /// </summary>
        public bool StopSysMain()
        {
            try
            {
                using var service = new ServiceController(SysMainServiceName);
                
                if (service.Status == ServiceControllerStatus.Running)
                {
                    Logger.Log("Parando serviço SysMain...", "INFO");
                    service.Stop();
                    service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(30));
                    Logger.Log("SysMain parado", "SUCCESS");
                    return true;
                }
                
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao parar SysMain: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Inicia o serviço SysMain
        /// </summary>
        public bool StartSysMain()
        {
            try
            {
                using var service = new ServiceController(SysMainServiceName);
                
                if (service.Status == ServiceControllerStatus.Stopped)
                {
                    Logger.Log("Iniciando serviço SysMain...", "INFO");
                    service.Start();
                    service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(30));
                    Logger.Log("SysMain iniciado", "SUCCESS");
                    return true;
                }
                
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao iniciar SysMain: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Desabilita SysMain permanentemente
        /// </summary>
        public bool DisableSysMain()
        {
            try
            {
                using var service = new ServiceController(SysMainServiceName);
                
                // Para o serviço
                if (service.Status == ServiceControllerStatus.Running)
                {
                    service.Stop();
                    service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(30));
                }

                // Desabilita via linha de comando
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "sc.exe",
                    Arguments = $"config {SysMainServiceName} start= disabled",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true
                };

                using var process = System.Diagnostics.Process.Start(psi);
                process?.WaitForExit();

                Logger.Log("SysMain desabilitado permanentemente", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao desabilitar SysMain: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Habilita SysMain permanentemente
        /// </summary>
        public bool EnableSysMain()
        {
            try
            {
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "sc.exe",
                    Arguments = $"config {SysMainServiceName} start= auto",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true
                };

                using var process = System.Diagnostics.Process.Start(psi);
                process?.WaitForExit();

                Logger.Log("SysMain habilitado", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao habilitar SysMain: {ex.Message}", "ERROR");
                return false;
            }
        }
    }
}
