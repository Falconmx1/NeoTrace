import asyncio
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os
from database import redis_client
import logging

logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self):
        self.webhook_urls = {
            'slack': os.getenv('SLACK_WEBHOOK_URL'),
            'discord': os.getenv('DISCORD_WEBHOOK_URL'),
            'telegram': os.getenv('TELEGRAM_BOT_TOKEN')
        }
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'sender_email': os.getenv('ALERT_EMAIL'),
            'sender_password': os.getenv('EMAIL_PASSWORD'),
            'receiver_emails': os.getenv('ALERT_RECIPIENTS', '').split(',')
        }
        
        # Configuración de alertas
        self.alert_config = {
            'malicious_ip': {
                'threshold': 50,  # Risk score mínimo
                'cooldown_minutes': 30,  # No repetir misma IP por 30 min
                'severity': 'high'
            },
            'suspicious_activity': {
                'threshold': 10,  # Alertas por minuto
                'time_window': 60,  # Segundos
                'severity': 'medium'
            },
            'system_health': {
                'cpu_threshold': 80,  # Porcentaje
                'memory_threshold': 90,  # Porcentaje
                'severity': 'critical'
            }
        }
        
        self.recent_alerts = {}  # Para cooldown de alertas
        self.alert_history = []
    
    async def send_alert(self, alert_type: str, data: Dict):
        """Envía alerta por todos los canales configurados"""
        alert_id = f"{alert_type}_{datetime.now().timestamp()}"
        
        # Verificar cooldown
        if alert_type in self.recent_alerts:
            last_alert = self.recent_alerts[alert_type]
            if (datetime.now() - last_alert).seconds < self.alert_config[alert_type]['cooldown_minutes'] * 60:
                return
        
        self.recent_alerts[alert_type] = datetime.now()
        
        # Formatear mensaje
        message = self._format_alert_message(alert_type, data)
        severity = self.alert_config[alert_type]['severity']
        
        # Enviar a todos los canales
        tasks = []
        
        if self.webhook_urls['slack']:
            tasks.append(self._send_slack(message, severity))
        
        if self.webhook_urls['discord']:
            tasks.append(self._send_discord(message, severity))
        
        if self.webhook_urls['telegram']:
            tasks.append(self._send_telegram(message))
        
        if self.email_config['sender_email'] and self.email_config['receiver_emails']:
            tasks.append(self._send_email(message, severity))
        
        # Guardar en Redis para persistencia
        await self._store_alert(alert_id, alert_type, message, severity)
        
        # Ejecutar en paralelo
        await asyncio.gather(*tasks)
        
        logger.info(f"Alerta enviada: {alert_type} - {severity}")
    
    def _format_alert_message(self, alert_type: str, data: Dict) -> str:
        """Formatea el mensaje según el tipo de alerta"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if alert_type == 'malicious_ip':
            ip = data.get('ip')
            risk_score = data.get('risk_score')
            classification = data.get('classification')
            country = data.get('country', 'Desconocido')
            explanation = data.get('ai_explanation', '')[:200]
            
            return f"""
🔴 **ALERTA DE SEGURIDAD** 🔴
━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ **Tiempo:** {timestamp}
🌐 **IP Maliciosa:** `{ip}`
⚠️ **Riesgo:** {risk_score}/100
🏷️ **Clasificación:** {classification}
📍 **País:** {country}

📝 **Análisis IA:**
{explanation}

🚨 **Acción recomendada:** Bloquear inmediatamente
━━━━━━━━━━━━━━━━━━━━━━━━━
            """
        
        elif alert_type == 'suspicious_activity':
            return f"""
⚠️ **ACTIVIDAD SOSPECHOSA** ⚠️
⏰ **Tiempo:** {timestamp}
📊 **IPs analizadas:** {data.get('total_ips')}
🔍 **Sospechosas:** {data.get('suspicious_count')}
⚡ **Tasa:** {data.get('rate')}/min

**Recomendación:** Monitorear tráfico
            """
        
        elif alert_type == 'system_health':
            return f"""
⚠️ **ALERTA DEL SISTEMA** ⚠️
⏰ **Tiempo:** {timestamp}
💻 **CPU:** {data.get('cpu_usage')}%
💾 **Memoria:** {data.get('memory_usage')}%
🔥 **Temperatura:** {data.get('temperature', 'N/A')}

**Recomendación:** Revisar recursos del servidor
            """
    
    async def _send_slack(self, message: str, severity: str):
        """Envía alerta a Slack"""
        color_map = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'good',
            'critical': 'danger'
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(severity, 'warning'),
                "text": message,
                "mrkdwn_in": ["text"]
            }]
        }
        
        try:
            response = requests.post(self.webhook_urls['slack'], json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error enviando a Slack: {e}")
    
    async def _send_discord(self, message: str, severity: str):
        """Envía alerta a Discord"""
        color_map = {
            'high': 0xFF0000,
            'medium': 0xFFA500,
            'low': 0x00FF00,
            'critical': 0x8B0000
        }
        
        payload = {
            "embeds": [{
                "title": "🚨 NeoTrace Alert",
                "description": message,
                "color": color_map.get(severity, 0xFFA500),
                "timestamp": datetime.now().isoformat()
            }]
        }
        
        try:
            response = requests.post(self.webhook_urls['discord'], json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error enviando a Discord: {e}")
    
    async def _send_telegram(self, message: str):
        """Envía alerta a Telegram"""
        token = self.webhook_urls['telegram']
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error enviando a Telegram: {e}")
    
    async def _send_email(self, message: str, severity: str):
        """Envía alerta por email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['receiver_emails'])
            msg['Subject'] = f"[NeoTrace] Alerta {severity.upper()} - {datetime.now().strftime('%H:%M')}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    async def _store_alert(self, alert_id: str, alert_type: str, message: str, severity: str):
        """Almacena alerta en Redis para historial"""
        alert_data = {
            'id': alert_id,
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'resolved': False
        }
        
        redis_client.hset(f"alerts:{alert_id}", mapping=alert_data)
        redis_client.lpush("alerts:list", alert_id)
        redis_client.expire(f"alerts:{alert_id}", 86400 * 7)  # 7 días
        
        self.alert_history.append(alert_data)
        
        # Mantener solo últimos 1000
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    async def check_system_health(self):
        """Monitorea salud del sistema y genera alertas"""
        import psutil
        
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        if cpu > self.alert_config['system_health']['cpu_threshold']:
            await self.send_alert('system_health', {
                'cpu_usage': cpu,
                'memory_usage': memory,
                'temperature': psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current')
            })
        
        if memory > self.alert_config['system_health']['memory_threshold']:
            await self.send_alert('system_health', {
                'cpu_usage': cpu,
                'memory_usage': memory,
                'temperature': psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current')
            })

# Instancia global
alert_system = AlertSystem()

async def monitor_suspicious_activity():
    """Monitorea actividad sospechosa en tiempo real"""
    from collections import defaultdict
    import time
    
    analysis_times = defaultdict(list)
    
    while True:
        current_time = time.time()
        
        # Limpiar tiempos antiguos
        for ip in list(analysis_times.keys()):
            analysis_times[ip] = [t for t in analysis_times[ip] if current_time - t < 60]
        
        # Verificar tasas sospechosas
        for ip, times in analysis_times.items():
            if len(times) > 10:  # Más de 10 análisis por minuto
                await alert_system.send_alert('suspicious_activity', {
                    'total_ips': len(analysis_times),
                    'suspicious_count': len([t for t in times if len(t) > 5]),
                    'rate': len(times),
                    'ip': ip
                })
        
        await asyncio.sleep(30)
