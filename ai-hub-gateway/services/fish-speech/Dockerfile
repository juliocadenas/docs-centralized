FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clonar Fish Speech
RUN git clone https://github.com/fishaudio/fish-speech.git /app/fish-speech

WORKDIR /app/fish-speech

RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart

COPY app.py /app/app.py

EXPOSE 8000

CMD ["uvicorn", "/app/app:app", "--host", "0.0.0.0", "--port", "8000"]