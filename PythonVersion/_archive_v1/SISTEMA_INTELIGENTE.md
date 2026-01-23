# 🧠 Sistema de Priorização INTELIGENTE

## ✅ ATIVADO AUTOMATICAMENTE!

O otimizador agora detecta **AUTOMATICAMENTE** qualquer programa que VOCÊ inicia e dá prioridade ALTA!

---

## 🎯 Como Funciona

### Detecção Automática:
```
Você abre um jogo?     → PRIORIDADE ALTA ⭐
Você abre um app?      → PRIORIDADE ALTA ⭐
Você abre navegador?   → PRIORIDADE BAIXA 🔽 (exceção)
Processo de sistema?   → SEM ALTERAÇÃO ⚙️
```

### Sistema Inteligente:
1. **Escaneia processos** a cada 10 segundos
2. **Detecta se foi iniciado por VOCÊ** (não é processo de sistema)
3. **Aplica prioridade automaticamente:**
   - ⭐ **ALTA**: Qualquer app/jogo que você abre
   - 🔽 **BAIXA**: Navegadores e apps de background

---

## 📋 Lista de Exceções (Sempre Prioridade Baixa)

Esses apps recebem prioridade baixa MESMO sendo iniciados por você:

- ✅ **Navegadores**: Chrome, Edge, Firefox, Opera
- ✅ **Background**: Discord, Spotify, Steam
- ✅ **Cloud**: OneDrive, Dropbox, Google Drive

**Motivo:** Esses apps rodam em background e podem travar o sistema se tiverem prioridade alta.

---

## 🎮 Exemplos Práticos

### Você abre um jogo:
```
[PRIORITY] ⭐ ALTA → seu_jogo.exe (PID: 12345)
```
→ Jogo recebe CPU e I/O prioritários instantaneamente!

### Chrome abre sozinho:
```
[PRIORITY] 🔽 BAIXA → chrome.exe (PID: 67890)
```
→ Chrome não vai travar seu jogo ou app importante!

### Você abre Photoshop/Blender/etc:
```
[PRIORITY] ⭐ ALTA → photoshop.exe (PID: 11111)
```
→ Renderização e trabalho com prioridade máxima!

---

## ⚙️ Configuração (Opcional)

Quer adicionar mais apps à lista de "sempre baixa prioridade"?

Edite `config.yaml`:

```yaml
auto_low_priority_apps:
  - "chrome.exe"
  - "discord.exe"
  - "seu_app_aqui.exe"  # Adicione aqui
```

---

## 🚀 Vantagens

### Antes (Manual):
```
❌ Você precisava configurar cada jogo/app
❌ Esquecia de adicionar novos programas
❌ Lista gigante de configuração
```

### Agora (Automático):
```
✅ QUALQUER app que você abre = Prioridade ALTA
✅ ZERO configuração necessária
✅ Funciona com programas novos automaticamente
✅ Sistema aprende sozinho
```

---

## 📊 O que você verá nos logs:

Quando você abrir um programa, verá:
```
[PRIORITY] ⭐ ALTA → MeuJogo.exe (PID: 12345)
[PRIORITY] ⭐ ALTA → Photoshop.exe (PID: 67890)
[PRIORITY] 🔽 BAIXA → chrome.exe (PID: 11111)
```

---

## ⚠️ Notas Importantes

1. **Processos de Sistema**: Nunca são alterados (segurança)
2. **Requer Admin**: Necessário para alterar prioridades
3. **Instantâneo**: Prioridade aplicada assim que app inicia
4. **Não afeta nada negativamente**: Só otimiza!

---

## 🎯 Quando Reiniciar o Otimizador

Para ativar esta funcionalidade:

1. **Ctrl+C** no otimizador atual
2. Execute **RUN_OPTIMIZER.bat** novamente
3. Observe os logs: `[PRIORITY]` aparecerá quando apps iniciarem

---

**Agora você NUNCA mais precisa configurar prioridades manualmente!** 🎉
