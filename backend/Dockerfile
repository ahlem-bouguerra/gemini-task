FROM mcr.microsoft.com/playwright:v1.57.0-noble

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

RUN playwright install chromium

# Create necessary directories
RUN mkdir -p /data/user_data /data/uploads /data/downloads



COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8000"]