
# Simple Dockerfile for the Streamlit mini-app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps (optional: build tools for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY eligibility_app.py .

# Default path for the registry file (can be overridden at runtime)
ENV REGISTRO_DMT_PATH=/data/registro_dmt.csv

# Create a volume mount point
VOLUME ["/data"]

EXPOSE 8501

CMD ["streamlit", "run", "eligibility_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# inizializza git
git init

# aggiunge tutti i file
git add .

# crea il primo commit
git commit -m "Initial commit: DMT eligibility app"

# rinomina il branch in main
git branch -M main

# collega il repo remoto (sostituisci l’URL con quello del tuo repository!)
git remote add origin https://github.com/TUO-USERNAME/dmt-eligibility-app.git

# invia i file su GitHub
git push -u origin main
