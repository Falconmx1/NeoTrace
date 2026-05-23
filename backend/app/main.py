from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai_engine import analyze_ip_with_ai
import requests

app = FastAPI(title="NeoTrace AI")

class IPRequest(BaseModel):
    ip: str

@app.post("/api/v1/analyze")
async def analyze_ip(request: IPRequest):
    # Obtener geolocalización básica
    geo = requests.get(f"https://ipinfo.io/{request.ip}/json").json()
    
    # Análisis con IA
    ai_result = analyze_ip_with_ai(request.ip, geo)
    
    return {
        "ip": request.ip,
        "location": {
            "city": geo.get("city"),
            "region": geo.get("region"),
            "country": geo.get("country"),
            "loc": geo.get("loc"),
            "isp": geo.get("org")
        },
        **ai_result
    }
