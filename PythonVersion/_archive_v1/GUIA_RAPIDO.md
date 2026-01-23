# Windows NVMe RAM Optimizer - Guia Rápido

## ✅ INSTALADO COM SUCESSO!

O otimizador está funcionando! Aqui está o que você precisa saber:

---

## 📊 O Que Está Acontecendo Agora

- **RAM Monitorada**: A cada 5 segundos verifica memória livre
- **Limpeza Automática**: Quando RAM livre < 1024MB, limpa automaticamente
- **Você verá**: `[CLEAN] Memória limpa: XXX MB liberados`

---

## ⚙️ Próximas Configurações

### 1. **Configurar CPU** (para estabilidade)

Edite `config.yaml`:

```yaml
cpu_control:
  max_frequency_percent: 80   # Limita CPU a 80% (mais estável)
  min_frequency_percent: 50   # Mantém CPU sempre ativa
```

### 2. **Ativar Stress Test** (carga constante)

```yaml
stress_test:
  enabled: true
  target_load_percent: 70     # Mantém 70% de carga constante
```

### 3. **Ajustar Threshold de Limpeza**

```yaml
standby_cleaner:
  threshold_mb: 2048          # Limpa quando < 2GB (mais agressivo)
```

---

## 🚀 Iniciar Automaticamente ao Ligar PC

Execute como **Administrador**:

```powershell
.\install_service.ps1
```

Isso cria uma tarefa no Windows que roda o otimizador automaticamente.

---

## 🖱️ Atalho na Área de Trabalho

**Criado!** Procure por `Windows Optimizer.lnk` na sua área de trabalho.

Clique duas vezes → Aceita admin → Otimizador inicia!

---

## 📝 Comandos Úteis

**Para o otimizador que está rodando**: `Ctrl+C`

**Rodar novamente**: Clique duplo no atalho ou execute:
```bash
python win_optimizer.py
```

---

## 🎯 Teste Sugerido

1. **Deixe rodando por alguns minutos**
2. **Abra vários programas pesados** (Chrome com muitas abas, etc)
3. **Observe a limpeza automática** quando RAM ficar baixa
4. **Configure CPU** se quiser reduzir velocidade para estabilidade

---

## ⚠️ Notas Importantes

- **Sempre rode como Administrador** (necessário para limpar RAM)
- **Edite config.yaml** para personalizar funcionamento
- **Temperatura**: Monitore CPU se ativar stress test
- **Auto-start**: Opcional, mas recomendado

---

**Localização dos arquivos:**
`C:\Users\Lucas Valério\.gemini\antigravity\scratch\WindowsNVMeOptimizer\PythonVersion\`
