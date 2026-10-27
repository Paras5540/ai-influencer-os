FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg fonts-noto-devanagari tzdata ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY web/requirements.txt ./web-requirements.txt
RUN pip install --no-cache-dir -r web-requirements.txt

COPY . .

ENV APP_DATA_DIR=/app/data \
    TZ=Asia/Kolkata \
    PYTHONUNBUFFERED=1
VOLUME ["/app/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
