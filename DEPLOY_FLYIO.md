# 🚀 Deploy del Agente de Citas en Fly.io — Guía desde cero

## ¿Qué es Fly.io?
Es un servicio de hosting gratuito que corre tu código dentro de un
contenedor Docker en la nube. A diferencia de Render, permite correr
procesos 24/7 sin que se duerman, y tiene 3GB de RAM gratis —
suficiente para Playwright + Chromium.

---

## Estructura de archivos que necesitás en tu repo

```
tu-repo/
├── agent.py          ← el agente con Playwright
├── notifier.py       ← tu notificador de Telegram (sin cambios)
├── config.py         ← lee variables de entorno (ver abajo)
├── requirements.txt  ← playwright y playwright-stealth
├── Dockerfile        ← le dice a Fly.io cómo armar el contenedor
└── fly.toml          ← configuración de Fly.io
```

---

## PASO 1 — Instalar flyctl (la herramienta de línea de comandos)

**En Windows**, abrí PowerShell y ejecutá:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://fly.io/install.ps1 | iex"
```

**En Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

Después cerrá y volvé a abrir la terminal para que reconozca el comando `fly`.

---

## PASO 2 — Crear cuenta en Fly.io

```bash
fly auth signup
```

Esto abre el navegador para registrarte. Podés usar tu cuenta de GitHub.
**No te pide tarjeta de crédito** para el plan gratuito.

Si ya tenés cuenta:
```bash
fly auth login
```

---

## PASO 3 — Adaptar config.py para leer variables de entorno

Tu `config.py` tiene que leer los secretos desde variables de entorno,
NO tenerlos hardcodeados en el código:

```python
import os

URL                = os.environ["URL"]
CHECK_INTERVAL_MIN = int(os.environ.get("CHECK_INTERVAL_MIN", "5"))
TELEGRAM_TOKEN     = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

# Si todavía usás estas variables en notifier.py:
# HEADLESS = True  ← esto ya no hace falta, siempre es True en la nube
```

---

## PASO 4 — Subir tu código a GitHub

Si todavía no tenés el repo en GitHub:

```bash
cd tu-carpeta-del-proyecto
git init
git add .
git commit -m "Agente citas Fly.io"
```

Después creá un repositorio nuevo en https://github.com/new y seguí
las instrucciones que te da GitHub para conectarlo.

---

## PASO 5 — Crear la app en Fly.io

Desde la carpeta de tu proyecto en la terminal:

```bash
fly launch
```

Te va a hacer algunas preguntas:
- **App name**: escribí `agente-citas-espana` (o el nombre que quieras)
- **Region**: elegí `mad` (Madrid) — es el más cercano al consulado
- **Would you like to set up a PostgreSQL database?**: No
- **Would you like to deploy now?**: No (primero cargamos los secretos)

Esto crea el archivo `fly.toml` automáticamente. Si ya tenés el
`fly.toml` de este repo, podés saltear este paso y ir directo al 6.

---

## PASO 6 — Cargar los secretos (variables de entorno)

Nunca pongas passwords o tokens en el código. Cargalos así:

```bash
fly secrets set URL="https://www.citaconsular.es/es/hosteds/widgetdefault/298f7f17f58c0836448a99edecf16e66a"
fly secrets set CHECK_INTERVAL_MIN="5"
fly secrets set TELEGRAM_TOKEN="tu_token_del_bot_aqui"
fly secrets set TELEGRAM_CHAT_ID="tu_chat_id_aqui"
```

Para verificar que quedaron guardados:
```bash
fly secrets list
```

---

## PASO 7 — Hacer el deploy

```bash
fly deploy
```

Esto va a:
1. Construir el contenedor Docker (tarda ~5 min la primera vez)
2. Instalar Chromium dentro del contenedor
3. Subir todo a Fly.io
4. Arrancar el agente

Vas a ver algo así al final:
```
==> Monitoring deployment
 1 desired, 1 placed, 1 healthy, 0 unhealthy
--> v1 deployed successfully
```

---

## PASO 8 — Ver los logs en tiempo real

```bash
fly logs
```

Deberías ver:
```
[2026-04-09 10:00:00] 🤖 Agente de citas iniciado
[2026-04-09 10:00:00] Intervalo: ~5 min | Headless: True
[2026-04-09 10:00:02] Navegando al widget...
[2026-04-09 10:00:08] 🖱️  Clickeando 'Continuar'...
[2026-04-09 10:00:12] ✓ Contenido detectado (245 chars)
[2026-04-09 10:00:12] ❌ Sin citas ('no hay horas disponibles'). Siguiente ciclo...
```

---

## Comandos útiles del día a día

```bash
fly logs              # Ver logs en tiempo real
fly status            # Estado de la app
fly secrets list      # Ver qué secretos están cargados
fly deploy            # Redesplegar después de cambios en el código
fly apps list         # Ver todas tus apps
fly scale show        # Ver recursos asignados
```

---

## ❓ Preguntas frecuentes

**¿Es realmente gratis?**
Sí. Fly.io tiene un free tier que incluye 3 máquinas shared-cpu-1x
con 256MB RAM cada una, o 1 máquina con más RAM. Para este agente
alcanza y sobra sin pagar nada.

**¿Se duerme como Render?**
No. Fly.io mantiene el proceso corriendo 24/7 sin necesidad de pings.

**¿Qué pasa si el agente se cae con un error?**
Fly.io lo reinicia automáticamente.

**¿Cómo actualizo el código?**
Hacés cambios en tu repo local y corrés `fly deploy` de nuevo.

**¿La región "mad" (Madrid) importa?**
Sí, un poco. Al estar en Europa la IP no va a ser bloqueada por
geolocalización como pasaba con Render (que está en Oregon, USA).
