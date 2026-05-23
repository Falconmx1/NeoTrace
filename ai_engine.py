import tensorflow as tf
import numpy as np
import joblib
import os
import requests
from groq import Groq
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar modelo TF Lite y scaler
interpreter = tf.lite.Interpreter(model_path="app/ip_classifier.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

scaler = joblib.load("app/scaler.pkl")

# Inicializar Groq (consigue tu API key gratis en console.groq.com)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", "tu-api-key-aqui"))

# Clases de IP
CLASSES = {0: "normal", 1: "sospechoso", 2: "malicioso"}

def extract_features(ip, geo_data, abuse_reports=0):
    """Extrae features para el modelo"""
    current_hour = datetime.now().hour
    
    # Detectar VPN/proxy con ipinfo.io (gratis)
    vpn = 0
    proxy = 0
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=2)
        data = response.json()
        if 'privacy' in data:
            vpn = 1 if data['privacy'].get('vpn') else 0
            proxy = 1 if data['privacy'].get('proxy') else 0
    except:
        pass
    
    # Países vistos (simulado, idealmente de DB histórica)
    paises_vistos = geo_data.get('previous_countries', 1)
    
    # Puertos abiertos (simulado, podrías escanear con scapy)
    puertos_abiertos = geo_data.get('open_ports', 0)
    
    features = np.array([[
        current_hour, vpn, proxy, paises_vistos, puertos_abiertos, abuse_reports
    ]])
    
    return scaler.transform(features)

def classify_with_tflite(features):
    """Clasifica IP con TensorFlow Lite"""
    interpreter.set_tensor(input_details[0]['index'], features.astype(np.float32))
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    class_id = np.argmax(output[0])
    confidence = np.max(output[0])
    return CLASSES[class_id], confidence, output[0].tolist()

def get_groq_explanation(ip, classification, confidence, geo_data):
    """Obtiene explicación en lenguaje natural de Groq"""
    prompt = f"""
    Eres un experto en ciberseguridad. Explica de forma técnica pero clara:
    
    IP: {ip}
    Clasificación: {classification} (confianza: {confidence:.1%})
    Ubicación: {geo_data.get('city', 'desconocida')}, {geo_data.get('country', 'desconocido')}
    ISP: {geo_data.get('org', 'desconocido')}
    
    Responde en español con:
    1. Por qué esta IP tiene ese nivel de riesgo
    2. Posibles usos (residencial, hosting, VPN, etc.)
    3. Recomendación de acción (bloquear, monitorear, ignorar)
    """
    
    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # modelo rápido y potente de Groq
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error con Groq: {e}")
        return "No se pudo obtener explicación de IA en este momento."

def analyze_ip_with_ai(ip, geo_data, abuse_reports=0):
    """Función principal que integra TF Lite + Groq"""
    
    # 1. Extraer features
    features = extract_features(ip, geo_data, abuse_reports)
    
    # 2. Clasificar con TF Lite
    classification, confidence, probabilities = classify_with_tflite(features)
    
    # 3. Generar explicación con Groq
    explanation = get_groq_explanation(ip, classification, confidence, geo_data)
    
    # 4. Calcular risk_score (0-100)
    risk_score = int(probabilities[2] * 100) if classification == "malicioso" else \
                 int(probabilities[1] * 70) if classification == "sospechoso" else \
                 int(probabilities[0] * 10)
    
    return {
        "ip": ip,
        "classification": classification,
        "confidence": round(confidence, 2),
        "risk_score": risk_score,
        "probabilities": {
            "normal": round(probabilities[0], 3),
            "sospechoso": round(probabilities[1], 3),
            "malicioso": round(probabilities[2], 3)
        },
        "ai_explanation": explanation,
        "features_used": {
            "hora": datetime.now().hour,
            "vpn_detectada": features[0][1] > 0.5,
            "proxy_detectado": features[0][2] > 0.5
        }
    }
