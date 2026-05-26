# =============================================================
# Tutor IA CEFIS - imagem unica (backend + estaticos + indice)
# =============================================================

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias do sistema (sqlite-vec ja vem com libs estaticas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Codigo da aplicacao
COPY app/ ./app/
COPY scripts/ ./scripts/

# Volumes externos (montados pelo docker-compose):
#   /app/Docs/output  -> catalogo extraido
#   /app/data         -> SQLite com o indice
RUN mkdir -p /app/Docs/output /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -fsS http://127.0.0.1:8000/api/status || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
