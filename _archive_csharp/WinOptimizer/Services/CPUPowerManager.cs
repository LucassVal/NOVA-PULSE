using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace WinOptimizer.Services
{
    /// <summary>
    /// Gerenciador de energia e frequência da CPU
    /// Permite limitar velocidade máxima do processador para estabilidade
    /// </summary>
    public class CPUPowerManager
    {
        [DllImport("powrprof.dll", SetLastError = true)]
        private static extern uint PowerSetActiveScheme(IntPtr UserRootPowerKey, ref Guid SchemeGuid);

        [DllImport("powrprof.dll", SetLastError = true)]
        private static extern uint PowerGetActiveScheme(IntPtr UserRootPowerKey, out IntPtr ActivePolicyGuid);

        [DllImport("powrprof.dll", SetLastError = true)]
        private static extern uint PowerWriteACValueIndex(IntPtr RootPowerKey, ref Guid SchemeGuid, 
            ref Guid SubGroupOfPowerSettingsGuid, ref Guid PowerSettingGuid, uint AcValueIndex);

        [DllImport("powrprof.dll", SetLastError = true)]
        private static extern uint PowerWriteDCValueIndex(IntPtr RootPowerKey, ref Guid SchemeGuid,
            ref Guid SubGroupOfPowerSettingsGuid, ref Guid PowerSettingGuid, uint DcValueIndex);

        // GUIDs do plano de energia
        private static readonly Guid GUID_PROCESSOR_SETTINGS_SUBGROUP = new Guid("54533251-82be-4824-96c1-47b60b740d00");
        private static readonly Guid GUID_PROCESSOR_THROTTLE_MAXIMUM = new Guid("bc5038f7-23e0-4960-96da-33abaf5935ec");
        private static readonly Guid GUID_PROCESSOR_THROTTLE_MINIMUM = new Guid("893dee8e-2bef-41e0-89c6-b55d0929964c");

        /// <summary>
        /// Define a frequência máxima da CPU (0-100%)
        /// </summary>
        public bool SetMaxCPUFrequency(int percentage)
        {
            if (percentage < 5 || percentage > 100)
            {
                Logger.Log($"Percentual inválido: {percentage}%. Deve estar entre 5-100%", "ERROR");
                return false;
            }

            try
            {
                Logger.Log($"Configurando frequência máxima da CPU para {percentage}%", "INFO");

                // Obtém o plano de energia ativo
                IntPtr activePolicyPtr;
                PowerGetActiveScheme(IntPtr.Zero, out activePolicyPtr);
                Guid activePolicyGuid = (Guid)Marshal.PtrToStructure(activePolicyPtr, typeof(Guid))!;
                Marshal.FreeHGlobal(activePolicyPtr);

                // Define o máximo (AC - plugado na tomada)
                PowerWriteACValueIndex(IntPtr.Zero, ref activePolicyGuid, 
                    ref GUID_PROCESSOR_SETTINGS_SUBGROUP, 
                    ref GUID_PROCESSOR_THROTTLE_MAXIMUM, 
                    (uint)percentage);

                // Define o máximo (DC - bateria)
                PowerWriteDCValueIndex(IntPtr.Zero, ref activePolicyGuid,
                    ref GUID_PROCESSOR_SETTINGS_SUBGROUP,
                    ref GUID_PROCESSOR_THROTTLE_MAXIMUM,
                    (uint)percentage);

                // Reaplica o plano para que as mudanças tenham efeito
                PowerSetActiveScheme(IntPtr.Zero, ref activePolicyGuid);

                Logger.Log($"Frequência máxima da CPU definida para {percentage}%", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao definir frequência: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Define a frequência mínima da CPU (0-100%)
        /// Útil para manter CPU sempre ativa
        /// </summary>
        public bool SetMinCPUFrequency(int percentage)
        {
            if (percentage < 0 || percentage > 100)
            {
                Logger.Log($"Percentual inválido: {percentage}%. Deve estar entre 0-100%", "ERROR");
                return false;
            }

            try
            {
                Logger.Log($"Configurando frequência mínima da CPU para {percentage}%", "INFO");

                IntPtr activePolicyPtr;
                PowerGetActiveScheme(IntPtr.Zero, out activePolicyPtr);
                Guid activePolicyGuid = (Guid)Marshal.PtrToStructure(activePolicyPtr, typeof(Guid))!;
                Marshal.FreeHGlobal(activePolicyPtr);

                PowerWriteACValueIndex(IntPtr.Zero, ref activePolicyGuid,
                    ref GUID_PROCESSOR_SETTINGS_SUBGROUP,
                    ref GUID_PROCESSOR_THROTTLE_MINIMUM,
                    (uint)percentage);

                PowerWriteDCValueIndex(IntPtr.Zero, ref activePolicyGuid,
                    ref GUID_PROCESSOR_SETTINGS_SUBGROUP,
                    ref GUID_PROCESSOR_THROTTLE_MINIMUM,
                    (uint)percentage);

                PowerSetActiveScheme(IntPtr.Zero, ref activePolicyGuid);

                Logger.Log($"Frequência mínima da CPU definida para {percentage}%", "SUCCESS");
                return true;
            }
            catch (Exception ex)
            {
                Logger.Log($"Erro ao definir frequência mínima: {ex.Message}", "ERROR");
                return false;
            }
        }

        /// <summary>
        /// Obtém temperatura atual da CPU (via WMI, nem sempre disponível)
        /// </summary>
        public double? GetCPUTemperature()
        {
            try
            {
                using var searcher = new System.Management.ManagementObjectSearcher(
                    @"root\WMI", "SELECT * FROM MSAcpi_ThermalZoneTemperature");

                foreach (System.Management.ManagementObject obj in searcher.Get())
                {
                    double temp = Convert.ToDouble(obj["CurrentTemperature"]);
                    // Converte de Kelvin * 10 para Celsius
                    return (temp - 2732) / 10.0;
                }
            }
            catch
            {
                // Temperatura não disponível via WMI
            }

            return null;
        }

        /// <summary>
        /// Obtém uso médio da CPU
        /// </summary>
        public float GetCPUUsage()
        {
            try
            {
                using var cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
                cpuCounter.NextValue(); // Primeira leitura é sempre 0
                System.Threading.Thread.Sleep(100);
                return cpuCounter.NextValue();
            }
            catch
            {
                return 0;
            }
        }

        /// <summary>
        /// Restaura configurações padrão (100% max, 5% min)
        /// </summary>
        public bool RestoreDefaults()
        {
            Logger.Log("Restaurando configurações padrão de CPU", "INFO");
            return SetMaxCPUFrequency(100) && SetMinCPUFrequency(5);
        }
    }
}
