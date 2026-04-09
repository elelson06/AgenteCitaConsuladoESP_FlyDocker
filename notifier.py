import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _base_url():
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram(message):
    """Envía mensaje de texto. Retorna True si fue exitoso."""
    try:
        r = requests.post(
            f"{_base_url()}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if r.ok:
            print("📨 Notificación Telegram enviada")
            return True
        print(f"⚠️  Error Telegram: {r.status_code} — {r.text}")
        return False
    except Exception as e:
        print(f"💥 No se pudo notificar: {e}")
        return False
