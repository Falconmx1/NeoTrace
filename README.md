# 🌐 NeoTrace – IP Tracker con Inteligencia Artificial

**NeoTrace** es una herramienta avanzada de rastreo IP que combina geolocalización precisa con análisis potenciado por IA.  
Ideal para pentesters, administradores de red y curiosos de la ciberseguridad.

## 🧠 Características con IA:
- 🎯 **Geolocalización precisa** (mapa + coordenadas + ISP)
- 🤖 **Detección de actividad sospechosa** (probabilidad de VPN, proxy, TOR, datacenter)
- 📊 **Predicción de comportamiento** según la IP (horarios de actividad, posible tipo de usuario)
- 🔍 **Análisis de riesgo** (score de 0 a 100)
- 🧬 **Búsqueda inversa** de dominios asociados
- 📡 **Datos en vivo** (ping, puertos abiertos opcional)

## 🛠️ Stack tecnológico:
- Frontend: React + Tailwind + Leaflet (mapas)
- Backend: Python (FastAPI) + Scapy
- IA: Modelo TensorFlow Lite / OpenAI function calling (detección de anomalías)
- Base de datos: Redis (caché) + PostgreSQL (historial)

## 🚀 Cómo usarlo (pronto):
```bash
git clone https://github.com/Falconmx1/NeoTrace.git
cd NeoTrace
docker-compose up
