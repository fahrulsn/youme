# Gunakan image Python yang ringan
FROM python:3.10-slim

# Install FFmpeg dan dependencies sistem
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory di dalam container
WORKDIR /app

# Copy requirements dan install library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi ke dalam container
COPY . .

# Buat folder downloads jika belum ada
RUN mkdir -p /app/downloads

# Expose port yang digunakan Flask
EXPOSE 8080

# Jalankan aplikasi menggunakan Gunicorn dengan worker Uvicorn
# app:app artinya (nama_file_python):(nama_variabel_flask)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]