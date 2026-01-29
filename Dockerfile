FROM mcr.microsoft.com/playwright:v1.57.0-noble

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Create a directory for user data (browser session)
RUN mkdir -p /app/user_data

COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python3", "gemini_process.py"]
