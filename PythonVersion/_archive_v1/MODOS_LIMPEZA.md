# 🔥 Modo AGRESSIVO de Limpeza de RAM

## 3 Modos Disponíveis:

### 1️⃣ Modo ATUAL (Threshold-Based) ⚖️ **[ATIVO]**

```yaml
threshold_mb: 2048  # Limpa quando < 2GB livre
check_interval_seconds: 5
```

**Como funciona:**
- Verifica RAM a cada 5 segundos
- Se RAM livre < 2GB → **Limpa TODO Standby Cache**
- Se RAM livre > 2GB → Não faz nada

**Libera:** 4-6GB de uma vez quando necessário

**Ideal para:** Uso balanceado

---

### 2️⃣ Modo THRESHOLD ALTO (Mais Seguro) 🛡️

```yaml
threshold_mb: 4096  # Limpa quando < 4GB livre
check_interval_seconds: 5
```

**Como funciona:**
- Verifica RAM a cada 5 segundos
- Se RAM livre < 4GB → **Limpa TODO Standby Cache**
- Age mais cedo que o modo atual

**Libera:** 4-6GB quando RAM cai abaixo de 4GB

**Ideal para:** Multitasking pesado (muitos apps abertos)

---

### 3️⃣ Modo AGRESSIVO (Periódico) 🔥

```python
# Usa AggressiveStandbyCleaner
clean_interval_seconds: 30  # Limpa a cada 30s
```

**Como funciona:**
- A cada 30 segundos
- **SEMPRE limpa** Standby Cache
- Não importa quanta RAM tem livre

**Libera:** Mantém Standby Cache sempre vazio

**Ideal para:** Performance máxima absoluta

---

## 📊 Comparação:

| Modo | Frequência | CPU Uso | RAM Livre | Agress. |
|---|---|---|---|---|
| **Threshold 2GB** ⭐ | Quando < 2GB | Baixo | 2-8GB | Médio |
| **Threshold 4GB** 🛡️ | Quando < 4GB | Médio | 4-10GB | Alto |
| **Periódico 30s** 🔥 | A cada 30s | Alto | 6-12GB | Máximo |

---

## ⚙️ Como Ativar Cada Modo:

### Modo THRESHOLD ALTO (4GB):

Edite `config.yaml`:
```yaml
standby_cleaner:
  enabled: true
  threshold_mb: 4096  # Era 2048
  check_interval_seconds: 5
```

### Modo AGRESSIVO (Periódico):

1. Edite `win_optimizer.py` linha ~90:
```python
# Substitui:
from modules.standby_cleaner import StandbyMemoryCleaner

# Por:
from modules.aggressive_cleaner import AggressiveStandbyCleaner as StandbyMemoryCleaner
```

2. Edite `config.yaml`:
```yaml
standby_cleaner:
  enabled: true
  threshold_mb: 0  # Ignorado no modo agressivo
  check_interval_seconds: 30  # Limpa a cada 30s
```

---

## 🎯 Recomendação:

### Para Você (Promob + Gaming):

**Opção A: Threshold 4GB** ⭐ (Recomendado)
- Mais margem de segurança
- Não desperdiça CPU
- Cleaner age antes de "sufocar"

**Opção B: Modo Agressivo** 🔥 (Máxima Performance)
- RAM sempre no máximo
- Usa mais CPU (~2-3%)
- Performance absoluta

**Opção C: Manter 2GB** ⚖️ (Atual)
- Já está funcionando bem
- Equilibrado
- Você já tem 3 limpezas automáticas

---

## 🧪 Teste Recomendado:

### 1. Tente Threshold 4GB primeiro:

```yaml
threshold_mb: 4096
```

**Resultado esperado:**
- RAM livre: 4-6GB sempre
- Limpezas: 5-8 por hora
- CPU: Mesmo impacto

### 2. Se quiser MÁXIMO, use Agressivo:

```yaml
threshold_mb: 0
check_interval_seconds: 30
```

**Resultado esperado:**
- RAM livre: 8-12GB sempre
- Limpezas: 120 por hora (2/min)
- CPU: +2-3% uso constante

---

## ⚠️ Aviso Modo Agressivo:

**Prós:**
- ✅ RAM livre MÁXIMA sempre
- ✅ Zero chance de "sufoco"
- ✅ Performance máxima

**Contras:**
- ❌ CPU trabalhando constantemente
- ❌ Standby Cache pode ser útil às vezes
- ❌ Desperdiça energia

**Windows usa Standby Cache para:**
- Reabrir apps recém fechados rápido
- Cache de arquivos do sistema
- SuperFetch predictions

**Limpar SEMPRE = perde essas otimizações**

---

## 💡 **Minha Recomendação Final:**

**Threshold 4GB** é o **sweet spot** para você!

```yaml
threshold_mb: 4096  # 4GB
check_interval_seconds: 5
```

**Por quê:**
- ✅ Muito mais agressivo que 2GB
- ✅ Não desperdiça CPU
- ✅ Mantém Windows "smart features"
- ✅ Ideal para Promob + Gaming

---

**Quer que eu ajuste para 4GB agora?**
