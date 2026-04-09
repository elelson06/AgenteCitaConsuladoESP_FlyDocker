import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def _base_url():
    return f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


async def send_telegram(message: str) -> bool:
    """
    Envía un mensaje de texto al chat configurado.
    Soporta formato Markdown básico (*negrita*, _cursiva_, `código`).
    Retorna True si el envío fue exitoso.
    """
    try:
        response = requests.post(
            f"{_base_url()}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        if response.ok:
            print("📨 Notificación Telegram enviada correctamente")
            return True
        else:
            print(f"⚠️  Error Telegram: {response.status_code} — {response.text}")
            return False
    except Exception as exc:
        print(f"💥 No se pudo enviar notificación: {exc}")
        return False


async def send_screenshot(path: str) -> bool:
    """
    Envía una imagen (captura de pantalla) al chat de Telegram.
    Útil para confirmar visualmente el estado del sitio en el momento de la alerta.
    """
    try:
        with open(path, "rb") as photo:
            response = requests.post(
                f"{_base_url()}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID},
                files={"photo": photo},
                timeout=15,
            )
        if response.ok:
            print("🖼️  Screenshot enviado a Telegram")
            return True
        else:
            print(f"⚠️  Error al enviar screenshot: {response.status_code}")
            return False
    except FileNotFoundError:
        print(f"⚠️  Screenshot no encontrado: {path}")
        return False
    except Exception as exc:
        print(f"💥 Error al enviar screenshot: {exc}")
        return False
