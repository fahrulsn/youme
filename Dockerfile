FROM python:3.10-slim

# Wajib install curl dan nodejs untuk memecahkan tantangan bot YouTube terbaru
RUN apt-get update && apt-get install -y ffmpeg curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Port Koyeb (sesuaikan dengan dashboard)
EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]