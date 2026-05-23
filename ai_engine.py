import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def get_ai_explanation(ip, risk_score, geo_data):
    prompt = f"Explica de forma técnica y concisa por qué la IP {ip} tiene un riesgo de {risk_score}/100. Datos: {geo_data}"
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
