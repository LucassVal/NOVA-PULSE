# 🔥 Guia de Undervolt - NVIDIA RTX 3050 Laptop

## Por Que Fazer Undervolt?

**RTX 3050 Laptop** tende a esquentar muito (80-85°C+) em jogos.

### Benefícios:
- ⚡ **-10°C a -15°C** temperatura
- 💰 **-15W a -20W** consumo
- 🎮 **FPS mais estáveis** (menos throttling)
- 🔇 **Ventoinhas mais silenciosas**
- ⏱️ **Maior vida útil** da GPU

---

## 🎯 Método Recomendado: MSI Afterburner

### Passo 1: Download e Instalação
1. https://www.msi.com/Landing/afterburner
2. Instale e abra o programa
3. Vá em **Settings** → **General** → Ative **Unlock voltage control**

### Passo 2: Abrir Curve Editor
- Pressione **Ctrl + F** → Abre gráfico de frequência/voltagem

### Passo 3: Encontrar o Sweet Spot

**Para RTX 3050 Laptop:**

| Configuração | Frequência | Voltagem | Resultado |
|---|---|---|---|
| **Stock** | 1800 MHz | 1000-1050mV | 80-85°C |
| **Conservador** | 1800 MHz | 925mV | ~73°C (-7°C) |
| **Balanceado** ⭐ | 1800 MHz | 875mV | ~70°C (-10°C) |
| **Agressivo** | 1800 MHz | 850mV | ~67°C (-13°C) |

**Recomendação: 875mV @ 1800 MHz**

### Passo 4: Aplicar a Curva

1. **No Curve Editor:**
   - Clique no ponto **875mV**
   - Arraste para cima até **1800 MHz**
   - Pressione **L** para travar essa frequência
   - Achate tudo acima de 875mV para 1800 MHz

2. **Aplicar:**
   - Botão **Apply** (✓)
   - Teste em jogo por 30 minutos

3. **Salvar:**
   - Se estável → **Save** → Perfil 1
   - Ative **Apply on startup**

---

## 🧪 Teste de Estabilidade

### Passo 1: Benchmark
```
- Furmark (5 minutos)
- Heaven Benchmark (10 minutos)
- Seu jogo favorito (30 minutos)
```

### Passo 2: Monitorar
- **MSI Afterburner OSD**: Mostra temperatura no jogo
- **HWiNFO64**: Monitora em segundo plano

### Sinais de Instabilidade:
- ❌ Artefatos visuais (linhas, flickering)
- ❌ Crash do jogo
- ❌ Tela preta
- ❌ Driver reset

**Se instável:** Aumente +25mV e teste novamente.

---

## 📊 Configurações Testadas pela Comunidade

### RTX 3050 Laptop (75W):
- **Conservador**: 1750 MHz @ 900mV
- **Balanceado**: 1800 MHz @ 875mV ⭐
- **Agressivo**: 1850 MHz @ 850mV

### RTX 3050 Laptop (60W TGP):
- **Conservador**: 1650 MHz @ 875mV
- **Balanceado**: 1700 MHz @ 850mV ⭐

---

## 🔧 Alternativa: Power Limit

Se não quiser mexer com voltagem, pode apenas **limitar o Power Limit**:

**MSI Afterburner:**
- Power Limit: **85%** (padrão 100%)
- Resultado: -5°C a -8°C, pequena perda de performance (~3%)

---

## 🐍 Integração com Python (Opcional)

Posso criar um módulo que aplica **Power Limit via pynvml**:

```python
import pynvml

pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)

# Limita power para 90% (aprox 67W se máximo é 75W)
pynvml.nvmlDeviceSetPowerManagementLimit(handle, 67000)  # 67W em mW
```

**Nota:** Isso NÃO é undervolt de voltagem, apenas limita potência máxima.

---

## ⚙️ Configuração Recomendada Final

### MSI Afterburner:
```
Core Clock: +0 (deixa no undervolt)
Memory Clock: +200 MHz (seguro para GDDR6)
Power Limit: 100% (deixa máximo, o undervolt já economiza)
Temp Limit: 83°C
Curve: 1800 MHz @ 875mV
```

### Resultado Esperado:
- **Temperatura**: 68-72°C (vs 80-85°C stock)
- **Performance**: 100% ou até +3% (sem throttling)
- **Consumo**: -15W a -20W
- **Ruído**: Ventoinhas 30-40% mais baixas

---

## ❓ FAQ

**Q: Posso danificar a GPU?**
A: Não! Undervolt REDUZ voltagem, é mais seguro que stock. O pior que pode acontecer é crash/instabilidade.

**Q: Vou perder garantia?**
A: Não! Undervolt não é permanente e não fica gravado na VBIOS.

**Q: Preciso fazer isso toda vez que ligar o PC?**
A: Não! MSI Afterburner tem **"Apply on startup"**.

**Q: Funciona em todos os RTX 3050?**
A: Sim, mas valores variam (silicon lottery). Comece conservador.

---

## 🎯 TL;DR - Quick Start

1. **Download MSI Afterburner**
2. **Ctrl + F** → Curve Editor
3. **875mV → 1800 MHz**
4. **Achata tudo acima**
5. **Apply + Test**
6. **Ganhe -10°C temperatura!**

---

**Sua RTX 3050 vai rodar muito mais fresca e silenciosa!** 🔥→❄️
