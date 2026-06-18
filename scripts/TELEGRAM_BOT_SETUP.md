# 🤖 Telegram Alert Bot - Guía de Instalación

El bot de Telegram monitorea el sistema 24/7 y envía alertas automáticas cuando:
- 🔴 El Gateway se cae
- 🔴 VRAM > 85% (crítico > 95%)
- 🔴 Servicios críticos offline (Ollama, TTS, STT, Rembg)
- 🔄 El servidor se reinicia (recuperación automática)

## Setup en 5 minutos

### 1. Crear el bot en Telegram
1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Dale un nombre: `AI Hub Madrid Bot`
4. Dale un username: `ai_hub_madrid_bot` (debe terminar en `_bot`)
5. **Copia el token** que te da (formato: `1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Obtener tu Chat ID
1. Envía cualquier mensaje a tu nuevo bot
2. Abre en el navegador:
   ```
   https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   ```
3. Busca `"chat":{"id":XXXXXXXXX}` — ese número es tu Chat ID

### 3. Configurar en el servidor (SSH)
```bash
ssh pepe@100.105.27.27

# Copiar el servicio
sudo cp /mnt/seagate/ai-hub-gateway/scripts/telegram-alert-bot.service /etc/systemd/system/

# Editar con tus credenciales
sudo nano /etc/systemd/system/telegram-alert-bot.service
# Cambiar:
#   Environment=TELEGRAM_BOT_TOKEN=tu_token_aqui
#   Environment=TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Activar
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-alert-bot

# Verificar
sudo systemctl status telegram-alert-bot
sudo journalctl -u telegram-alert-bot -f  # ver logs en vivo
```

### 4. Probar el bot
```bash
# En el servidor
cd /mnt/seagate/ai-hub-gateway
TELEGRAM_BOT_TOKEN=tu_token TELEGRAM_CHAT_ID=tu_id python scripts/telegram_alert_bot.py test
```

Deberías recibir un mensaje en Telegram con el estado del sistema.

### 5. Verificar que está corriendo
```bash
sudo systemctl status telegram-alert-bot
# Debe decir "active (running)"
```

## Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `python telegram_alert_bot.py` | Inicia el loop de monitoreo |
| `python telegram_alert_bot.py test` | Envía un mensaje de prueba |
| `python telegram_alert_bot.py status` | Imprime estado en consola (sin Telegram) |

## Alertas que enviará

| Alerta | Condición | Cooldown |
|--------|-----------|----------|
| 🚨 Gateway caído | `:9000/v1/status` no responde | 10 min |
| 🔴 VRAM Crítica | VRAM ≥ 95% | 10 min |
| 🟡 VRAM Alta | VRAM ≥ 85% | 10 min |
| ⚠️ Servicio offline | Ollama/TTS/STT/Rembg caídos | 10 min |
| 🔄 Reinicio detectado | boot_id cambió | Una vez por reboot |

El bot checa cada **2 minutos** y no reenvía la misma alerta dentro de 10 minutos (anti-spam).