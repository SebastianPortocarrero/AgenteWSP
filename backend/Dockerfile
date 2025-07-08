FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential python3-dev libxml2-dev libxslt1-dev libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar config y scripts si se usan en tiempo de ejecución
COPY config /app/config
COPY scripts /app/scripts

COPY requirements.txt ./

RUN pip install --upgrade pip && \
#instalar dependencias
    pip install --no-cache-dir -r requirements.txt && \
    pip install hypercorn
# Copiar el código fuente
COPY src /app/src

# Establece el directorio de trabajo
WORKDIR /app/src

# Puerto expuesto
EXPOSE 8080

# Establece el PYTHONPATH
ENV PYTHONPATH=/app

# Comando de arranque
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8080", "--worker-class", "asyncio"]
