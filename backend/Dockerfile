FROM python:3.10-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential python3-dev libxml2-dev libxslt1-dev libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia el directorio config y el archivo de requerimientos de src
COPY config /app/config
COPY src/requerimientos.txt /app/src/requerimientos.txt

# Establece el directorio de trabajo a src para la instalación de dependencias
WORKDIR /app/src

# Instala dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requerimientos.txt hypercorn

# Copia el código fuente de src al directorio de trabajo actual (/app/src)
COPY src /app/src

# Expone el puerto
EXPOSE 8080

# Establece la variable de entorno PYTHONPATH para que Python encuentre los módulos
ENV PYTHONPATH=/app

# Define el comando para ejecutar la aplicación
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8080", "--worker-class", "asyncio"]
