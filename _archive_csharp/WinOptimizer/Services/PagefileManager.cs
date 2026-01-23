using System;
using System.Management;
using System.Linq;
using Microsoft.Win32;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Gerenciador de arquivo de paginação (Pagefile)
    /// </summary>
    public class PagefileManager
    {
        public class PagefileInfo
        {
            public string DriveLetter { get; set; } = "";
            public long InitialSizeMB { get; set; }
            public long MaximumSizeMB { get; set; }
            public bool IsManaged { get; set; }
        }

        /// <summary>
        /// Obtém informação atual do pagefile
        /// </summary>
        public PagefileInfo GetCurrentPagefile()
        {
            try
            {
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_PageFileSetting");
                var pagefiles = searcher.Get();

                if (pagefiles.Count == 0)
                {
                    return new PagefileInfo { IsManaged = true };
                }

                foreach (ManagementObject pagefile in pagefiles)
                {
                    string name = pagefile["Name"]?.ToString() ?? "";
                    int initialSize = Convert.ToInt32(pagefile["InitialSize"] ?? 0);
                    int maxSize = Convert.ToInt32(pagefile["MaximumSize"] ?? 0);

                    return new PagefileInfo
                    {
                        DriveLetter = name.Length > 0 ? name[0].ToString() : "C",
                        InitialSizeMB = initialSize,
                        MaximumSizeMB = maxSize,
                        IsManaged = initialSize == 0 && maxSize == 0
                    };
                }
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao obter info do pagefile: {ex.Message}", "ERROR");
            }

            return new PagefileInfo { IsManaged = true };
        }

        /// <summary>
        /// Configura pagefile com tamanho fixo
        /// </summary>
        public bool SetPagefile(string driveLetter, long sizeMB)
        {
            try
            {
                Logger.Log($"Configurando pagefile: {driveLetter}: {sizeMB}MB", "INFO");

                // Remove pagefiles existentes
                RemoveAllPagefiles();

                // Cria novo pagefile
                using var mc = new ManagementClass("Win32_PageFileSetting");
                using var pageFile = mc.CreateInstance();
                
                if (pageFile == null)
                {
                    Logger.Log("Falha ao criar instância de pagefile", "ERROR");
                    return false;
                }

                pageFile["Name"] = $"{driveLetter}:\\pagefile.sys";
                pageFile["InitialSize"] = (uint)sizeMB;
                pageFile["MaximumSize"] = (uint)sizeMB;
                pageFile.Put();

                Logger.Log($"Pagefile configurado com sucesso: {sizeMB}MB em {driveLetter}:", "SUCCESS");
                Logger.Log("REINICIALIZAÇÃO NECESSÁRIA para aplicar mudanças", "WARN");

                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao configurar pagefile: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Remove todos os pagefiles configurados
        /// </summary>
        private void RemoveAllPagefiles()
        {
            try
            {
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_PageFileSetting");
                foreach (ManagementObject pagefile in searcher.Get())
                {
                    pagefile.Delete();
                }
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao remover pagefiles: {ex.Message}", "ERROR");
            }
        }

        /// <summary>
        /// Calcula tamanho recomendado baseado na RAM instalada
        /// </summary>
        public long GetRecommendedSize(double multiplier = 1.0)
        {
            try
            {
                var totalRAM = GC.GetGCMemoryInfo().TotalAvailableMemoryBytes / 1024 / 1024;
                return (long)(totalRAM * multiplier);
            }
            catch
            {
                return 16384; // Padrão: 16GB
            }
        }

        /// <summary>
        /// Retorna drives NVMe disponíveis (drives rápidos)
        /// </summary>
        public string[] GetNVMeDrives()
        {
            try
            {
                using var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_DiskDrive WHERE MediaType LIKE '%SSD%' OR MediaType LIKE '%NVMe%'");
                var drives = new System.Collections.Generic.List<string>();

                foreach (ManagementObject disk in searcher.Get())
                {
                    // Associa com partições
                    string deviceId = disk["DeviceID"]?.ToString() ?? "";
                    using var partitionSearcher = new ManagementObjectSearcher(
                        $"ASSOCIATORS OF {{Win32_DiskDrive.DeviceID='{deviceId}'}} WHERE AssocClass=Win32_DiskDriveToDiskPartition");

                    foreach (ManagementObject partition in partitionSearcher.Get())
                    {
                        using var logicalDiskSearcher = new ManagementObjectSearcher(
                            $"ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='{partition["DeviceID"]}'}} WHERE AssocClass=Win32_LogicalDiskToPartition");

                        foreach (ManagementObject logicalDisk in logicalDiskSearcher.Get())
                        {
                            string driveLetter = logicalDisk["Name"]?.ToString() ?? "";
                            if (!string.IsNullOrEmpty(driveLetter) && driveLetter.Length >= 1)
                            {
                                drives.Add(driveLetter[0].ToString());
                            }
                        }
                    }
                }

                return drives.Distinct().ToArray();
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao detectar NVMe: {ex.Message}", "ERROR");
                return new[] { "C" };
            }
        }

        /// <summary>
        /// Desabilita gerenciamento automático de pagefile
        /// </summary>
        public bool DisableAutomaticManagement()
        {
            try
            {
                using var key = Registry.LocalMachine.OpenSubKey(
                    @"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
                    true);

                if (key != null)
                {
                    key.SetValue("PagingFiles", new string[] { }, RegistryValueKind.MultiString);
                    Logger.Log("Gerenciamento automático de pagefile desabilitado", "SUCCESS");
                    return true;
                }
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao desabilitar auto-management: {ex.Message}", "ERROR");
            }

            return false;
        }
    }
}
