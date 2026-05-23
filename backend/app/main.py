from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from cache_manager import cache_system
from websocket_manager import manager, realtime_ip_scanner, continuous_network_monitor
from abuseipdb_client import build_real_dataset
from advanced_model import train_advanced_model
import asyncio

app = FastAPI(title="NeoTrace AI Pro")

# Endpoint WebSocket para escaneo en tiempo real
@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get('command')
            
            if command == 'scan_network':
                network = data.get('network', '192.168.1.0/24')
                await realtime_ip_scanner(websocket, network)
            
            elif command == 'monitor_ips':
                ips = data.get('ips', [])
                interval = data.get('interval', 30)
                await continuous_network_monitor(websocket, ips, interval)
            
            elif command == 'analyze_ip':
                ip = data.get('ip')
                
                # Verificar caché primero
                cached = cache_system.get_cached_result(ip)
                if cached:
                    await manager.send_message({'type': 'cached', 'result': cached}, websocket)
                else:
                    from ai_engine import analyze_ip_with_ai
                    result = analyze_ip_with_ai(ip, {})
                    cache_system.cache_result(ip, result)
                    await manager.send_message({'type': 'analysis', 'result': result}, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint para entrenar modelo con datos reales
@app.post("/api/v1/train")
async def train_model():
    asyncio.create_task(build_real_dataset())
    asyncio.create_task(train_advanced_model())
    return {"status": "Entrenamiento iniciado en background"}
