FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Dependencias mínimas del sistema
RUN apt-get update && apt-get install -y \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright instala sus propias dependencias del sistema automáticamente
RUN playwright install chromium --with-deps

# Copiar código
COPY agent.py .
COPY notifier.py .
COPY config.py .

CMD ["python", "agent.py"]
