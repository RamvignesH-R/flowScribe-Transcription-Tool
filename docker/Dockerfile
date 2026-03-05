FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create output folders
RUN mkdir -p product_created/transcripts product_created/logs

EXPOSE 7860

CMD ["bash", "-c", "uvicorn app.backend.main:app --host 0.0.0.0 --port 8502 & streamlit run app/frontend/dashboard.py --server.port 7860 --server.address 0.0.0.0 --server.headless true"]