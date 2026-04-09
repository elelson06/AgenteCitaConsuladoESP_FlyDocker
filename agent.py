"""
Agente de citas — Consulado General de España en Córdoba
Versión Playwright (browser headless) para Fly.io

Cómo funciona:
  1. Abre el widget con un browser real (para pasar hCaptcha/Cloudflare)
  2. Clickea "Continuar" si aparece
  3. Analiza el contenido de la página
  4. Si hay citas → notifica por Telegram con screenshot
  5. Si no hay nada → espera el intervalo y reintenta
"""

import asyncio
import random
from datetime import datetime

from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
    _STEALTH_MODE = "async"
except ImportError:
    try:
        from playwright_stealth import Stealth
        _STEALTH_MODE = "new"
    except ImportError:
        _STEALTH_MODE = "none"
        print("⚠️  playwright-stealth no disponible, continuando sin stealth")

from notifier import send_telegram, send_screenshot
from config import URL, CHECK_INTERVAL_MIN

# ─────────────────────────────────────────────
#  Botón de la pantalla intermedia
# ─────────────────────────────────────────────
CONTINUE_SELECTORS = [
    "button:has-text('Continuar')",
    "button:has-text('Continue')",
    "input[type='button'][value*='ontinuar']",
    "input[type='button'][value*='ontinue']",
    "input[type='submit'][value*='ontinuar']",
    "input[type='submit'][value*='ontinue']",
    "a:has-text('Continuar')",
    "a:has-text('Continue')",
]

# ─────────────────────────────────────────────
#  Frases que confirman que NO hay citas
# ─────────────────────────────────────────────
NO_CITA_TEXTS = [
    "no hay horas disponibles",
    "no hay citas disponibles",
    "no existen citas",
    "no quedan citas",
    "inténtelo de nuevo dentro de",
    "there are no appointments",
    "no appointments available",
    "servicio no disponible",
    "fuera de servicio",
]

LOAD_WAIT_TIMEOUT = 40
MIN_BODY_LENGTH = 50


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _filename_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M")


async def wait_for_content(page) -> bool:
    """
    Espera hasta que el body tenga al menos MIN_BODY_LENGTH caracteres.
    Polling cada 500ms hasta LOAD_WAIT_TIMEOUT segundos.
    """
    deadline = asyncio.get_event_loop().time() + LOAD_WAIT_TIMEOUT
    last_len = 0

    while asyncio.get_event_loop().time() < deadline:
        try:
            text = await page.inner_text("body")
            text = text.strip()
            current_len = len(text)

            if current_len != last_len:
                print(f"[{_now()}] ⏳ Cargando... ({current_len} chars)")
                last_len = current_len

            if current_len >= MIN_BODY_LENGTH:
                print(f"[{_now()}] ✓ Contenido detectado ({current_len} chars)")
                return True
        except Exception:
            pass

        await asyncio.sleep(0.5)

    print(f"[{_now()}] ⏱️  Timeout ({LOAD_WAIT_TIMEOUT}s). Body final: {last_len} chars.")
    return False


async def check_cita() -> str:
    async with async_playwright() as p:
        print(f"[{_now()}] Lanzando Chromium...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-software-rasterizer",
                "--disable-background-networking",
                "--shm-size=256mb",
            ]
        )
        print(f"[{_now()}] Chromium lanzado OK, creando contexto...")
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="es-AR",
        )
        page = await context.new_page()

        if _STEALTH_MODE == "async":
            await stealth_async(page)
        elif _STEALTH_MODE == "new":
            await Stealth().apply_stealth_async(page)

        try:
            print(f"[{_now()}] Browser iniciado OK")
            print(f"[{_now()}] Navegando al widget...")
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # ── 1. Click en "Continuar" si aparece ───────────────────────
            for sel in CONTINUE_SELECTORS:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        print(f"[{_now()}] 🖱️  Clickeando 'Continuar'...")
                        await btn.click()
                        await asyncio.sleep(random.uniform(1.5, 2.5))
                        break
                except Exception:
                    continue

            # ── 2. Esperar contenido real ─────────────────────────────────
            content_loaded = await wait_for_content(page)

            body_text = ""
            try:
                body_text = (await page.inner_text("body")).strip().lower()
            except Exception:
                pass

            # ── 3. ¿Sin citas? ────────────────────────────────────────────
            for phrase in NO_CITA_TEXTS:
                if phrase in body_text:
                    print(f"[{_now()}] ❌ Sin citas ('{phrase}'). Siguiente ciclo...")
                    return "no_citas"

            # ── 4. Body vacío → página no cargó ──────────────────────────
            if not content_loaded and len(body_text) < MIN_BODY_LENGTH:
                print(f"[{_now()}] 🔄 Página no cargó (body vacío). Ciclo descartado.")
                return "cargando"

            # ── 5. Contenido diferente → posible cita ────────────────────
            ts = _filename_ts()
            screenshot_path = f"/tmp/cita_disponible_{ts}.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            print(f"[{_now()}] ✅ Pantalla diferente detectada. Screenshot: {screenshot_path}")

            await send_telegram(
                f"🚨 *POSIBLE DISPONIBILIDAD DE CITA*\n\n"
                f"Se detectó una pantalla diferente a 'sin citas'.\n\n"
                f"🏛️ Consulado General de España - Córdoba\n"
                f"🔗 {URL}\n"
                f"⏰ {_now()}\n\n"
                f"Revisá el screenshot adjunto y entrá al link cuanto antes."
            )
            await send_screenshot(screenshot_path)
            return "posible_cita"

        except Exception as exc:
            print(f"[{_now()}] 💥 Error: {exc}")
            return "error"

        finally:
            await browser.close()


async def main():
    print(f"[{_now()}] 🤖 Agente de citas iniciado")
    print(f"[{_now()}] Intervalo: ~{CHECK_INTERVAL_MIN} min | Headless: True")
    print("─" * 55)

    while True:
        result = await check_cita()
        print(f"[{_now()}] Resultado: {result}")

        wait_sec = CHECK_INTERVAL_MIN * 60 + random.uniform(-30, 30)
        print(f"[{_now()}] Próxima revisión en {wait_sec / 60:.1f} min")
        print("─" * 55)
        await asyncio.sleep(wait_sec)


if __name__ == "__main__":
    asyncio.run(main())
