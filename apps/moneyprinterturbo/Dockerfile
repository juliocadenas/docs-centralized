# ============================================================
# MoneyPrinterTurbo - Dockerfile para AI Hub Madrid
# Basado en el repo oficial FujiwaraChoki/MoneyPrinterTurbo
# Adaptado para usar servicios locales (Ollama, Piper, Whisper)
# ============================================================
FROM python:3.10-slim

# Dependencias del sistema + FFmpeg (crítico para video)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clonar MoneyPrinterTurbo del repo oficial
RUN git clone https://github.com/FujiwaraChoki/MoneyPrinterTurbo.git /app && \
    rm -rf /app/.git

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelo Whisper small (para subtítulos, ~480MB)
# Si falla, la app usa edge-tts como fallback
RUN python -c "import whisper; whisper.load_model('small')" 2>/dev/null || \
    echo "Whisper model will download on first use"

# Crear directorios
RUN mkdir -p /app/projects /storage/videos /storage/audio /storage/output

EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=60s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

# Iniciar la UI de Streamlit
CMD ["streamlit", "run", "webui/StreamlitUI.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]