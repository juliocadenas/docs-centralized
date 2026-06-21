FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    piper-tts \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    fastapi

COPY app.py .

# Descargar voces Piper durante build
RUN mkdir -p /voices && \
    pip install --no-cache-dir piper-phonemize && \
    python -c "from piper.voice import PiperVoice; print('Piper ready')"

ENV PIPER_VOICES=/voices

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]