# Imagen base oficial de Python
FROM python:3.11-slim

# Evitar preguntas interactivas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ── Dependencias del sistema que necesita Chromium ───────────────────────────
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ── Instalar dependencias Python ─────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Instalar solo Chromium (Firefox y WebKit no los necesitamos) ─────────────
RUN playwright install chromium
RUN playwright install-deps chromium

# ── Copiar el código del agente ───────────────────────────────────────────────
COPY agent.py .
COPY notifier.py .
COPY config.py .

# ── Comando de inicio ─────────────────────────────────────────────────────────
CMD ["python", "agent.py"]
