#!/usr/bin/env python3
"""
AI Hub Madrid - Telegram Alert Bot
Monitors system health and sends alerts to Telegram.

Setup:
1. Create bot with @BotFather on Telegram → get TELEGRAM_BOT_TOKEN
2. Send a message to your bot, then visit:
   https://api.telegram.org/bot<TOKEN>/getUpdates → get chat_id
3. Set environment variables or edit config below:
   export TELEGRAM_BOT_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
4. Run as systemd service or cron.

Alerts sent on:
- Gateway down
- VRAM > 85%
- Any critical service offline
- System reboot detected
"""
import os, sys, time, json, requests, subprocess, logging
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GATEWAY_URL = "http://localhost:9000/v1"
CHECK_INTERVAL = 120  # 2 minutes
VRAM_ALERT_THRESHOLD = 85  # percent
VRAM_CRITICAL_THRESHOLD = 95  # percent

# Services that MUST be online (always_on)
CRITICAL_SERVICES = {
    "ollama": "http://localhost:11434",
    "piper_tts": "http://localhost:8010",
    "whisper_stt": "http://localhost:8020",
    "rembg": "http://localhost:8050",
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("ai-hub-telegram-bot")

# ============================================================
# State tracking
# ============================================================
_last_alert = {}  # alert_type -> timestamp (to avoid spamming)
_last_boot_id = None
ALERT_COOLDOWN = 600  # Don't re-alert same issue within 10 min


def send_telegram(message: str, parse_mode="HTML"):
    """Send a message to Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        log.warning("Telegram credentials not set - skipping alert")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": parse_mode}
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            log.info("Telegram alert sent")
            return True
        else:
            log.error(f"Telegram API error: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        log.error(f"Telegram send error: {e}")
        return False


def should_alert(alert_type: str) -> bool:
    """Check if we should alert (cooldown logic)."""
    now = time.time()
    last = _last_alert.get(alert_type, 0)
    if now - last > ALERT_COOLDOWN:
        _last_alert[alert_type] = now
        return True
    return False


def check_gateway() -> bool:
    """Check if Gateway is responding."""
    try:
        r = requests.get(f"{GATEWAY_URL}/status", timeout=10)
        return r.status_code == 200
    except:
        return False


def check_vram() -> dict:
    """Check GPU VRAM usage. Returns {'used_pct': int, 'used_mb': int, 'total_mb': int}."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            used_mb = int(parts[0])
            total_mb = int(parts[1])
            return {"used_pct": round(used_mb / total_mb * 100), "used_mb": used_mb, "total_mb": total_mb}
    except:
        pass
    return {"used_pct": 0, "used_mb": 0, "total_mb": 0}


def check_services() -> list:
    """Check critical services. Returns list of (name, url, is_online)."""
    results = []
    for name, url in CRITICAL_SERVICES.items():
        try:
            r = requests.get(url, timeout=5)
            results.append((name, url, r.status_code < 500))
        except:
            results.append((name, url, False))
    return results


def check_boot_id() -> bool:
    """Detect if system rebooted since last check."""
    global _last_boot_id
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            boot_id = f.read().strip()
        if _last_boot_id is None:
            _last_boot_id = boot_id
            return False
        elif _last_boot_id != boot_id:
            old = _last_boot_id
            _last_boot_id = boot_id
            return True
        return False
    except:
        return False


def get_uptime() -> str:
    """Get human-readable uptime."""
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        hours = int(secs // 3600)
        mins = int((secs % 3600) // 60)
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h {mins}m"
        return f"{hours}h {mins}m"
    except:
        return "unknown"


def run_monitor_loop():
    """Main monitoring loop."""
    log.info("=" * 50)
    log.info("AI Hub Madrid - Telegram Alert Bot started")
    log.info(f"Check interval: {CHECK_INTERVAL}s")
    log.info(f"VRAM alert threshold: {VRAM_ALERT_THRESHOLD}%")
    log.info(f"Critical services: {list(CRITICAL_SERVICES.keys())}")
    if BOT_TOKEN and CHAT_ID:
        send_telegram(
            f"🤖 <b>AI Hub Bot iniciado</b>\n\n"
            f"🖥️ Servidor: NAB9 (Madrid)\n"
            f"⏱️ Uptime: {get_uptime()}\n"
            f"🔔 Monitoreando: Gateway + {len(CRITICAL_SERVICES)} servicios críticos"
        )
    else:
        log.warning("⚠️ TELEGRAM_BOT_TOKEN/CHAT_ID not set - running in dry-run mode")
    log.info("=" * 50)

    while True:
        try:
            # 1. Check boot (reboot recovery alert)
            if check_boot_id():
                if should_alert("reboot"):
                    msg = (
                        f"🔄 <b>Reinicio detectado</b>\n\n"
                        f"El servidor NAB9 se ha reiniciado.\n"
                        f"⏱️ Uptime actual: {get_uptime()}"
                    )
                    send_telegram(msg)

            # 2. Check Gateway
            if not check_gateway():
                if should_alert("gateway_down"):
                    send_telegram(
                        f"🚨 <b>GATEWAY CAÍDO</b>\n\n"
                        f"El AI Hub Gateway (:9000) no responde.\n"
                        f"Revisa: <code>systemctl status ai-hub-gateway</code>"
                    )
            else:
                _last_alert.pop("gateway_down", None)  # Clear alert if recovered

            # 3. Check VRAM
            vram = check_vram()
            if vram["used_pct"] >= VRAM_CRITICAL_THRESHOLD:
                if should_alert("vram_critical"):
                    send_telegram(
                        f"🔴 <b>VRAM CRÍTICA</b>\n\n"
                        f"VRAM: {vram['used_mb']}MB / {vram['total_mb']}MB ({vram['used_pct']}%)\n"
                        f"⚠️ Riesgo de OOM inminente.\n"
                        f"Revisa procesos: <code>nvidia-smi</code>"
                    )
            elif vram["used_pct"] >= VRAM_ALERT_THRESHOLD:
                if should_alert("vram_high"):
                    send_telegram(
                        f"🟡 <b>VRAM Alta</b>\n\n"
                        f"VRAM: {vram['used_mb']}MB / {vram['total_mb']}MB ({vram['used_pct']}%)"
                    )
            else:
                _last_alert.pop("vram_high", None)
                _last_alert.pop("vram_critical", None)

            # 4. Check critical services
            services = check_services()
            offline = [(n, u) for n, u, online in services if not online]
            if offline:
                if should_alert("service_offline"):
                    names = "\n".join(f"  ❌ <b>{n}</b> ({u})" for n, u in offline)
                    send_telegram(
                        f"⚠️ <b>Servicios críticos caídos</b>\n\n{names}\n\n"
                        f"Revisa: <code>systemctl status ai-hub-*</code>"
                    )
            else:
                _last_alert.pop("service_offline", None)

        except Exception as e:
            log.error(f"Monitor loop error: {e}")

        time.sleep(CHECK_INTERVAL)


def send_test():
    """Send a test alert."""
    vram = check_vram()
    services = check_services()
    online_count = sum(1 for _, _, online in services if online)

    msg = (
        f"🧪 <b>Test de AI Hub Bot</b>\n\n"
        f"🖥️ <b>Servidor:</b> NAB9 (Madrid)\n"
        f"⏱️ <b>Uptime:</b> {get_uptime()}\n"
        f"🎮 <b>VRAM:</b> {vram['used_mb']}MB / {vram['total_mb']}MB ({vram['used_pct']}%)\n"
        f"📡 <b>Gateway:</b> {'✅ Online' if check_gateway() else '❌ Offline'}\n"
        f"🔧 <b>Servicios críticos:</b> {online_count}/{len(services)} online\n"
        f"\n💬 Todo funciona correctamente!"
    )
    success = send_telegram(msg)
    if success:
        print("✅ Test message sent to Telegram!")
    else:
        print("❌ Failed to send test message")


def send_status():
    """Print status without Telegram (for testing)."""
    vram = check_vram()
    services = check_services()
    print(f"Gateway: {'✅' if check_gateway() else '❌'}")
    print(f"VRAM: {vram['used_mb']}MB / {vram['total_mb']}MB ({vram['used_pct']}%)")
    for name, url, online in services:
        print(f"  {name}: {'✅' if online else '❌'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        if not BOT_TOKEN or not CHAT_ID:
            print("❌ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first!")
            print("   export TELEGRAM_BOT_TOKEN='your_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")
            sys.exit(1)
        send_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        send_status()
    else:
        run_monitor_loop()