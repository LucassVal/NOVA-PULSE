using System;
using System.Windows.Forms;
using System.Drawing;
using WinOptimizer.Services;

namespace WinOptimizer
{
    public class ConfigurationForm : Form
    {
        private OptimizerConfig? _config;
        private CPUPowerManager? _cpuPowerManager;
        private CPUStressTest? _stressTest;

        private NumericUpDown? _cpuMaxFreqNumeric;
        private NumericUpDown? _cpuMinFreqNumeric;
        private NumericUpDown? _stressLoadNumeric;
        private CheckBox? _stressEnabledCheckbox;
        private Button? _applyButton;
        private Button? _restoreDefaultsButton;

        public ConfigurationForm(OptimizerConfig? config, CPUPowerManager? cpuManager, CPUStressTest? stressTest)
        {
            _config = config;
            _cpuPowerManager = cpuManager;
            _stressTest = stressTest;

            InitializeUI();
        }

        private void InitializeUI()
        {
            Text = "Configurações Avançadas";
            Size = new Size(600, 500);
            StartPosition = FormStartPosition.CenterParent;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;

            int yPos = 20;

            // === CPU FREQUENCY SECTION ===
            var cpuFreqLabel = new Label
            {
                Text = "⚡ Controle de Frequência da CPU",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                Location = new Point(20, yPos),
                AutoSize = true
            };
            Controls.Add(cpuFreqLabel);
            yPos += 35;

            // CPU Max Frequency
            var maxFreqLabel = new Label
            {
                Text = "Frequência Máxima da CPU (%):",
                Location = new Point(40, yPos),
                AutoSize = true
            };
            Controls.Add(maxFreqLabel);

            _cpuMaxFreqNumeric = new NumericUpDown
            {
                Location = new Point(350, yPos - 3),
                Size = new Size(80, 25),
                Minimum = 20,
                Maximum = 100,
                Value = 100,
                Increment = 5
            };
            Controls.Add(_cpuMaxFreqNumeric);

            var maxFreqInfo = new Label
            {
                Text = "💡 Reduza para limitar velocidade e melhorar estabilidade",
                ForeColor = Color.Gray,
                Location = new Point(40, yPos + 25),
                AutoSize = true,
                Font = new Font("Segoe UI", 8)
            };
            Controls.Add(maxFreqInfo);
            yPos += 60;

            // CPU Min Frequency
            var minFreqLabel = new Label
            {
                Text = "Frequência Mínima da CPU (%):",
                Location = new Point(40, yPos),
                AutoSize = true
            };
            Controls.Add(minFreqLabel);

            _cpuMinFreqNumeric = new NumericUpDown
            {
                Location = new Point(350, yPos - 3),
                Size = new Size(80, 25),
                Minimum = 5,
                Maximum = 100,
                Value = 5,
                Increment = 5
            };
            Controls.Add(_cpuMinFreqNumeric);

            var minFreqInfo = new Label
            {
                Text = "💡 Aumente para manter CPU sempre ativa (ex: 50% = sempre rodando)",
                ForeColor = Color.Gray,
                Location = new Point(40, yPos + 25),
                AutoSize = true,
                Font = new Font("Segoe UI", 8)
            };
            Controls.Add(minFreqInfo);
            yPos += 60;

            // === STRESS TEST SECTION ===
            var stressLabel = new Label
            {
                Text = "🔥 Stress Test Controlado (Manter CPU Estável)",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                Location = new Point(20, yPos),
                AutoSize = true
            };
            Controls.Add(stressLabel);
            yPos += 35;

            _stressEnabledCheckbox = new CheckBox
            {
                Text = "Habilitar Stress Test Contínuo",
                Location = new Point(40, yPos),
                AutoSize = true,
                Checked = _stressTest?.IsRunning ?? false
            };
            _stressEnabledCheckbox.CheckedChanged += StressEnabledCheckbox_CheckedChanged;
            Controls.Add(_stressEnabledCheckbox);
            yPos += 30;

            var stressLoadLabel = new Label
            {
                Text = "Carga Desejada (%):",
                Location = new Point(40, yPos),
                AutoSize = true
            };
            Controls.Add(stressLoadLabel);

            _stressLoadNumeric = new NumericUpDown
            {
                Location = new Point(350, yPos - 3),
                Size = new Size(80, 25),
                Minimum = 20,
                Maximum = 95,
                Value = 70,
                Increment = 5,
                Enabled = _stressEnabledCheckbox.Checked
            };
            Controls.Add(_stressLoadNumeric);

            var stressInfo = new Label
            {
                Text = "💡 Mantém CPU em carga constante para estabilidade térmica\n" +
                       "    Recomendado: 60-75% para uso contínuo sem superaquecimento",
                ForeColor = Color.Gray,
                Location = new Point(40, yPos + 25),
                AutoSize = true,
                Font = new Font("Segoe UI", 8)
            };
            Controls.Add(stressInfo);
            yPos += 75;

            // === WARNING ===
            var warningPanel = new Panel
            {
                Location = new Point(20, yPos),
                Size = new Size(540, 60),
                BackColor = Color.FromArgb(255, 255, 200),
                BorderStyle = BorderStyle.FixedSingle
            };
            
            var warningLabel = new Label
            {
                Text = "⚠️ ATENÇÃO: Alterações na frequência da CPU afetam o plano de energia do Windows.\n" +
                       "Teste com valores conservadores primeiro. Monitore a temperatura!",
                Location = new Point(10, 10),
                Size = new Size(520, 40),
                Font = new Font("Segoe UI", 8, FontStyle.Bold),
                ForeColor = Color.DarkRed
            };
            warningPanel.Controls.Add(warningLabel);
            Controls.Add(warningPanel);
            yPos += 75;

            // === BUTTONS ===
            _applyButton = new Button
            {
                Text = "✓ Aplicar Configurações",
                Location = new Point(20, yPos),
                Size = new Size(200, 40),
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                BackColor = Color.FromArgb(0, 120, 215),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat
            };
            _applyButton.Click += ApplyButton_Click;
            Controls.Add(_applyButton);

            _restoreDefaultsButton = new Button
            {
                Text = "↺ Restaurar Padrões",
                Location = new Point(240, yPos),
                Size = new Size(150, 40),
                Font = new Font("Segoe UI", 9)
            };
            _restoreDefaultsButton.Click += RestoreDefaultsButton_Click;
            Controls.Add(_restoreDefaultsButton);

            var closeButton = new Button
            {
                Text = "Fechar",
                Location = new Point(410, yPos),
                Size = new Size(150, 40),
                Font = new Font("Segoe UI", 9)
            };
            closeButton.Click += (s, e) => Close();
            Controls.Add(closeButton);
        }

        private void StressEnabledCheckbox_CheckedChanged(object? sender, EventArgs e)
        {
            if (_stressLoadNumeric != null)
            {
                _stressLoadNumeric.Enabled = _stressEnabledCheckbox?.Checked ?? false;
            }
        }

        private void ApplyButton_Click(object? sender, EventArgs e)
        {
            try
            {
                // Aplica frequência máxima
                int maxFreq = (int)(_cpuMaxFreqNumeric?.Value ?? 100);
                _cpuPowerManager?.SetMaxCPUFrequency(maxFreq);

                // Aplica frequência mínima
                int minFreq = (int)(_cpuMinFreqNumeric?.Value ?? 5);
                _cpuPowerManager?.SetMinCPUFrequency(minFreq);

                // Controla stress test
                if (_stressEnabledCheckbox?.Checked ?? false)
                {
                    int stressLoad = (int)(_stressLoadNumeric?.Value ?? 70);
                    
                    if (_stressTest?.IsRunning ?? false)
                    {
                        _stressTest?.AdjustLoad(stressLoad);
                    }
                    else
                    {
                        _stressTest?.Start(stressLoad);
                    }
                }
                else
                {
                    _stressTest?.Stop();
                }

                MessageBox.Show(
                    "Configurações aplicadas com sucesso!\n\n" +
                    $"• CPU Máx: {maxFreq}%\n" +
                    $"• CPU Mín: {minFreq}%\n" +
                    $"• Stress: {(_stressEnabledCheckbox?.Checked ?? false ? "Ativo" : "Desativado")}",
                    "Sucesso",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao aplicar configurações:\n{ex.Message}",
                    "Erro",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private void RestoreDefaultsButton_Click(object? sender, EventArgs e)
        {
            var result = MessageBox.Show(
                "Restaurar configurações padrão?\n\n" +
                "Isto irá:\n" +
                "• Restaurar CPU para 100% máx / 5% mín\n" +
                "• Parar o stress test\n",
                "Confirmar",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question
            );

            if (result == DialogResult.Yes)
            {
                _cpuPowerManager?.RestoreDefaults();
                _stressTest?.Stop();
                
                _cpuMaxFreqNumeric!.Value = 100;
                _cpuMinFreqNumeric!.Value = 5;
                _stressEnabledCheckbox!.Checked = false;
                _stressLoadNumeric!.Value = 70;

                MessageBox.Show("Configurações padrão restauradas!", "Sucesso");
            }
        }
    }
}
