# USAR PYTHON 3.11 OFICIAL SLIM
FROM python:3.11-slim

# Evitar escritura de archivos .pyc y forzar buffer de stdout
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PORT=8080

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     curl     git     && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Exponer el puerto de Cloud Run (8080)
EXPOSE 8080

# Comando de inicio de Streamlit configurado para Google Cloud Run
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
