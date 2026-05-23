from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from ai_engine import analyze_ip_with_ai

app = FastAPI(title="NeoTrace AI", description="IP Tracker con TensorFlow Lite + Groq")

class IPRequest(BaseModel):
    ip: str

@app.post("/api/v1/analyze")
async def analyze(request: IPRequest):
    # Validar IP
    if not request.ip.replace('.', '').isdigit():
        raise HTTPException(400, "IP inválida")
    
    # Obtener datos base
    try:
        geo_response = requests.get(f"https://ipinfo.io/{request.ip}/json", timeout=5)
        geo_data = geo_response.json()
    except:
        geo_data = {"city": "desconocida", "country": "desconocido", "org": "desconocido"}
    
    # Obtener reports de AbuseIPDB (opcional, necesitas API key)
    # abuse_reports = get_abuse_reports(request.ip)
    abuse_reports = 0  # Por ahora
    
    # Análisis completo con IA
    result = analyze_ip_with_ai(request.ip, geo_data, abuse_reports)
    
    return result

@app.get("/api/v1/health")
async def health():
    return {"status": "NeoTrace AI activo", "modelo": "TF Lite + Groq"}
