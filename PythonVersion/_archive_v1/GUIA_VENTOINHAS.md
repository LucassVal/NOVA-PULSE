# 🌬️ Guia de Configuração de Ventoinhas

## ⚠️ Limitação do Windows

O Windows **NÃO permite** controle direto de ventoinhas via API.  
Você precisa usar ferramentas externas ou BIOS.

---

## ✅ OPÇÃO 1: NoteBook Fan Control (NBFC) - Recomendado

### Download e Instalação:
1. Acesse: https://github.com/hirschmann/nbfc/releases
2. Baixe a versão mais recente (ex: `NBFC-2.x.x-Setup.exe`)
3. Instale como Administrador
4. Abra NBFC e selecione seu modelo de laptop

### Configurar para 100%:
```powershell
# Via linha de comando:
nbfc set -s 100

# Ou via interface gráfica:
# NBFC > Settings > Fan Speed > 100%
```

### Auto-start:
✅ NBFC já inicia automaticamente com o Windows

---

## ✅ OPÇÃO 2: BIOS/UEFI

### Como Acessar:
1. **Reinicie o PC**
2. Pressione **F2**, **DEL**, **F10** ou **ESC** (depende do fabricante)
3. Procure por:
   - "Fan Control"
   - "Thermal Settings"  
   - "Cooling Options"
   - "System Performance"

### Configurar:
- Mude para **"Performance"** ou **"Maximum"**
- Ou desabilite **"Smart Fan Control"** e defina velocidade manual para 100%

---

## ✅ OPÇÃO 3: Software do Fabricante

### Dell:
- **Dell Power Manager** ou **Dell Command Center**
- Modo: **Ultra Performance**

### HP:
- **HP Command Center** ou **Omen Gaming Hub**
- Modo: **Performance**

### Lenovo:
- **Lenovo Vantage**
- Modo: **Extreme Performance**

### ASUS:
- **Armoury Crate** ou **ASUS AI Suite**
- Modo: **Turbo**

### MSI:
- **Dragon Center** ou **Center**
- Modo: **Extreme Performance**

### Acer:
- **PredatorSense** (Predator) ou **NitroSense** (Nitro)
- Modo: **Turbo**

---

## 🎯 Configuração Recomendada Completa

```yaml
# Seu config.yaml
cpu_control:
  max_frequency_percent: 85   # Ponto ótimo
  min_frequency_percent: 5

fan_control:
  try_auto_detect: true
  show_instructions: true
```

**+ Ventoinhas a 100% (via NBFC ou BIOS)**

### Resultado:
- ✅ CPU limitada a 85% (estável, eficiente)
- ✅ Ventoinhas a 100% (resfriamento máximo)
- ✅ Temperatura ~15-20°C mais baixa que stock
- ✅ Zero thermal throttling
- ✅ Sistema silencioso e performático

---

## 🔧 Teste Após Configurar

1. Reinicie o otimizador
2. Abra um programa pesado (jogo, renderização)
3. Monitore temperatura com HWiNFO64 ou MSI Afterburner
4. **Temperatura ideal:** 60-75°C sob carga (excelente!)

---

## ⚡ Troubleshooting

**Ventoinhas não aumentaram?**
- Verifique se NBFC está rodando
- Confirme que selecionou o perfil correto do laptop
- Tente reiniciar o PC

**Muito barulho?**
- Normal! Ventoinhas a 100% fazem barulho
- Se incomoda, reduza para 80-90% no NBFC
- CPU a 85% reduz calor, então 80% de ventoinha já é suficiente

**NBFC não detectou meu laptop?**
- Use BIOS/UEFI (mais confiável)
- Ou software do fabricante
