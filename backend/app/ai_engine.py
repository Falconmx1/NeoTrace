import requests
import random
from datetime import datetime

def analyze_ip_with_ai(ip, geo_data):
    """Analiza IP con IA híbrida (reglas + API gratuita)"""
    risk_score = 0
    reasons = []
    
    # 1. Detectar VPN/Proxy por API gratuita (ipinfo.io)
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        data = response.json()
        if 'privacy' in data:
            if data['privacy'].get('vpn'):
                risk_score += 30
                reasons.append("VPN detectada")
            if data['privacy'].get('proxy'):
                risk_score += 25
                reasons.append("Proxy detectado")
    except:
        pass
    
    # 2. Análisis geográfico (múltiples cambios = sospechoso)
    if geo_data.get('previous_ips'):
        risk_score += len(geo_data['previous_ips']) * 5
    
    # 3. Horarios inusuales (actividad 2 AM - 5 AM)
    current_hour = datetime.now().hour
    if 2 <= current_hour <= 5:
        risk_score += 20
        reasons.append("Actividad en horario inusual")
    
    # 4. IA generativa explicativa (simulada, luego con Groq/OpenAI)
    ai_insight = f"IP {ip} con riesgo {risk_score}/100. " + \
                 ("Alta probabilidad de actividad automatizada." if risk_score > 50 else "Comportamiento normal.")
    
    return {
        "risk_score": min(risk_score, 100),
        "reasons": reasons,
        "ai_insight": ai_insight,
        "ip_type": "VPN/Proxy" if risk_score > 40 else "Residencial/Estándar"
    }
