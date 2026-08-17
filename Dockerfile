FROM python:3.11-slim

# Instalar LibreOffice headless y fuentes básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Gunicorn con timeout de 120s por si un documento pesado tarda en convertir
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "2", "--timeout", "120", "app:app"]