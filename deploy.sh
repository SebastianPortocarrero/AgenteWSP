#!/bin/bash

echo "🚀 Desplegando aiagentvistony.com..."

# Compilar frontend
echo "📦 Compilando frontend..."
cd FrontTony
npm run build:prod
cd ..

# Copiar archivos del frontend a nginx
echo "📁 Copiando archivos del frontend..."
sudo cp -r FrontTony/dist/* /var/www/html/

# Construir y ejecutar backend con Docker
echo "🐳 Construyendo backend..."
cd AgenteTony
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d

echo "✅ Despliegue completado!"
echo "🌐 Tu sitio estará disponible en https://aiagentvistony.com"

# Instalar certificado SSL con Let's Encrypt (opcional)
echo "🔒 ¿Quieres instalar certificado SSL gratis? (y/n)"
read ssl_response
if [ "$ssl_response" = "y" ]; then
    sudo apt update
    sudo apt install certbot python3-certbot-nginx -y
    sudo certbot --nginx -d aiagentvistony.com -d www.aiagentvistony.com
fi 