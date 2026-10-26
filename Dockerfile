FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/data

WORKDIR /app

# Dépendances d'abord : cette couche est mise en cache tant que
# requirements.txt ne change pas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# Utilisateur non-root + dossier pour la base SQLite (monté en volume)
RUN useradd --create-home appuser \
    && mkdir -p /data \
    && chown -R appuser /data /app
USER appuser
VOLUME /data

EXPOSE 8050

# Docker marque le conteneur "unhealthy" si /health ne répond pas 200
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health', timeout=3)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "src.main:server"]
