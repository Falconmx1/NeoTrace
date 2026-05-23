#!/bin/bash

echo "🚀 Inicializando sistema de alertas de NeoTrace..."

# Crear directorios necesarios
mkdir -p prometheus grafana/dashboards grafana/datasources alertmanager

# Configurar alertas en backend
docker-compose exec backend python -c "
from app.alert_system import alert_system
import asyncio

async def init():
    await alert_system.send_alert('system_health', {
        'cpu_usage': 0,
        'memory_usage': 0,
        'temperature': 'N/A'
    })
    print('✅ Sistema de alertas inicializado')

asyncio.run(init())
"

# Configurar webhook de prueba (Opcional)
echo "🔔 Configurando webhook de prueba (si tienes Discord/Slack)"
read -p "URL de Discord Webhook (opcional): " discord_url
if [ ! -z "$discord_url" ]; then
    curl -X POST http://localhost:8000/api/v1/webhook/subscribe \
        -H "Content-Type: application/json" \
        -d "{
            \"url\": \"$discord_url\",
            \"events\": [\"malicious_ip\", \"suspicious_activity\"],
            \"headers\": {}
        }"
    echo "✅ Webhook de Discord configurado"
fi

echo "🎯 Dashboard disponible en: http://localhost:3001 (admin/neotrace2026)"
echo "📊 Prometheus: http://localhost:9090"
echo "🚨 Alertas en tiempo real activas"
