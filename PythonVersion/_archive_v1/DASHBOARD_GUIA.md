# 📊 Dashboard Visual - Guia de Uso

## Interface do Dashboard

Quando você rodar o otimizador, verá um dashboard visual completo:

```
╔═══════════════════════════════════════════════════════════════╗
║ ⚡ WINDOWS OPTIMIZER DASHBOARD | 13:30:45 | ● ATIVO           ║
╚═══════════════════════════════════════════════════════════════╝

┌─ 🖥️  CPU & GPU ───────────────┬─ 💾  Memória & Status ─────────┐
│                                │                                │
│ CPU                            │ MEMÓRIA RAM                    │
│   Uso         45.2% ████████░  │   Uso         68.5% ███████░   │
│   Temperatura 72°C             │   Livre       5.1 GB / 16.0 GB │
│   Frequência  3.74 GHz         │   Limpezas    12 automáticas   │
│   Limite      85% (otimizado)  │                                │
│                                │ OTIMIZAÇÕES                    │
│ GPU                            │   Standby Cleaner    ● Ativo   │
│   Uso         32.1% ██████░    │   Smart Priority     ● Ativo   │
│   Temperatura 65°C             │   CPU Limit          ● 85%     │
│   VRAM        2048 / 8192 MB   │   SysMain            ● Desab.  │
│                                │                                │
└────────────────────────────────┴────────────────────────────────┘

┌─ 🎯  Sistema Inteligente ─────────────────────────────────────┐
│ Priorização Inteligente                                       │
│ Processos do usuário são priorizados automaticamente          │
│ ⭐ 8 processos alta | 🔽 12 processos baixa                    │
└───────────────────────────────────────────────────────────────┘
```

## O Que Você Vê

### 🖥️ Painel CPU & GPU:
- **CPU Uso**: Porcentagem de uso com barra visual colorida
  - Verde < 70%
  - Amarelo 70-90%
  - Vermelho > 90%
- **CPU Temperatura**: Temperatura atual do processador
- **CPU Frequência**: GHz atual (máximo ~3.74 GHz a 85%)
- **CPU Limite**: Seu limite configurado (85% = otimizado)
- **GPU**: Se tiver placa NVIDIA, mostra uso, temperatura e VRAM

### 💾 Painel Memória & Status:
- **RAM Uso**: Porcentagem e barra visual
- **RAM Livre**: GB disponível / GB total
- **Limpezas**: Quantas vezes o cleaner limpou automaticamente
- **Status de Otimizações**: 
  - ● Verde = Ativo
  - ● Amarelo = Limitado
  - ● Vermelho = Desabilitado

### 🎯 Rodapé - Sistema Inteligente:
- **Apps Alta Prioridade**: Quantos processos estão priorizados
- **Apps Baixa Prioridade**: Quantos processos com prioridade baixa

## Cores

- 🟢 **Verde**: Normal/Bom
- 🟡 **Amarelo**: Atenção/Moderado
- 🔴 **Vermelho**: Alto/Crítico

## Atualização

O dashboard atualiza **automaticamente a cada 0.5 segundos**!

## Como Parar

Pressione **Ctrl+C** para encerrar o otimizador.

---

**Agora seu otimizador tem interface visual profissional!** 🎉
