FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Dependencias sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clonar LivePortrait
RUN git clone https://github.com/KwaiVGI/LivePortrait.git /app/LivePortrait

WORKDIR /app/LivePortrait

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    gradio

# Modelo cache via volume mount
ENV MODEL_DIR=/models

EXPOSE 7860

CMD ["python", "app.py", "--port", "7860", "--host", "0.0.0.0"]