FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    realesrgan \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    pillow \
    numpy

COPY app.py .

# Pre-descargar modelos durante build
RUN python -c "from realesrgan import RealESRGANer; RealESRGANer(scale=4, model_path='RealESRGAN_x4plus.pth', model=None, half=True)"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]