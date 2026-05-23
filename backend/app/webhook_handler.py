from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import hmac
import hashlib

app = FastAPI()

class WebhookConfig(BaseModel):
    url: str
    events: List[str]  # ['malicious_ip', 'suspicious_activity', 'system_health']
    secret: Optional[str] = None
    headers: Optional[dict] = {}

webhook_subscriptions = []

@app.post("/api/v1/webhook/subscribe")
async def subscribe_webhook(config: WebhookConfig, background_tasks: BackgroundTasks):
    """Registra un webhook para recibir alertas"""
    webhook_subscriptions.append(config)
    background_tasks.add_task(test_webhook, config)
    return {"status": "subscribed", "id": len(webhook_subscriptions) - 1}

async def test_webhook(config: WebhookConfig):
    """Prueba la conexión del webhook"""
    import requests
    test_payload = {
        "type": "test",
        "message": "NeoTrace webhook connected successfully",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        headers = config.headers or {}
        if config.secret:
            signature = hmac.new(
                config.secret.encode(),
                json.dumps(test_payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = signature
        
        response = requests.post(config.url, json=test_payload, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")

async def dispatch_webhook(alert_type: str, data: dict):
    """Envía alerta a todos los webhooks suscritos"""
    for subscription in webhook_subscriptions:
        if alert_type in subscription.events:
            payload = {
                "type": alert_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "source": "NeoTrace"
            }
            
            try:
                headers = subscription.headers or {}
                if subscription.secret:
                    signature = hmac.new(
                        subscription.secret.encode(),
                        json.dumps(payload).encode(),
                        hashlib.sha256
                    ).hexdigest()
                    headers['X-Webhook-Signature'] = signature
                
                import requests
                response = requests.post(
                    subscription.url,
                    json=payload,
                    headers=headers,
                    timeout=3
                )
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Webhook dispatch failed: {e}")
