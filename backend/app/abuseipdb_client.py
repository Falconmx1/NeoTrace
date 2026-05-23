import requests
import os
from datetime import datetime, timedelta
from database import SessionLocal, IPDataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY", "tu-api-key-aqui")
HEADERS = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}

def fetch_abuse_reports(ip, max_age_days=90):
    """Obtener reports reales de AbuseIPDB"""
    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        params = {
            'ipAddress': ip,
            'maxAgeInDays': max_age_days,
            'verbose': True
        }
        response = requests.get(url, headers=HEADERS, params=params, timeout=5)
        data = response.json()
        
        if 'data' in data:
            return {
                'abuse_score': data['data']['abuseConfidenceScore'],
                'total_reports': data['data']['totalReports'],
                'categories': [cat['id'] for cat in data['data'].get('reports', [])],
                'last_report': data['data'].get('lastReportedAt'),
                'country': data['data'].get('countryCode'),
                'isp': data['data'].get('isp')
            }
    except Exception as e:
        logger.error(f"Error fetching AbuseIPDB: {e}")
    return None

def build_real_dataset(days_to_collect=7, max_ips=10000):
    """Construir dataset real desde AbuseIPDB y otras fuentes"""
    session = SessionLocal()
    
    # 1. IPs maliciosas (de AbuseIPDB con score alto)
    malicious_ips = []
    for page in range(1, 11):  # 10 páginas
        try:
            url = "https://api.abuseipdb.com/api/v2/blacklist"
            params = {'confidenceMinimum': 90, 'limit': 100}
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            data = response.json()
            for entry in data.get('data', []):
                malicious_ips.append({
                    'ip': entry['ipAddress'],
                    'abuse_count': entry['abuseConfidenceScore'],
                    'label': 2  # malicioso
                })
        except:
            break
    
    # 2. IPs sospechosas (score medio)
    suspicious_ips = []
    for page in range(1, 6):
        try:
            params = {'confidenceMinimum': 50, 'confidenceMaximum': 89, 'limit': 100}
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            data = response.json()
            for entry in data.get('data', []):
                suspicious_ips.append({
                    'ip': entry['ipAddress'],
                    'abuse_count': entry['abuseConfidenceScore'],
                    'label': 1  # sospechoso
                })
        except:
            break
    
    # 3. IPs normales (de IPinfo o rangos conocidos)
    normal_ips = [
        '8.8.8.8', '8.8.4.4', '1.1.1.1', '208.67.222.222', '208.67.220.220',  # DNS
        '31.13.79.246', '157.240.22.35',  # Facebook
        '142.250.185.46', '172.217.168.46',  # Google
        '52.84.0.0/16',  # AWS CDN (rango)
    ]
    
    # Guardar en BD
    for ip_data in malicious_ips + suspicious_ips:
        # Extraer features reales de cada IP
        features = extract_real_features(ip_data['ip'])
        dataset_entry = IPDataset(
            ip=ip_data['ip'],
            features=features,
            label=ip_data['label'],
            abuse_count=ip_data['abuse_count'],
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        session.merge(dataset_entry)  # upsert
    
    for ip in normal_ips:
        features = extract_real_features(ip)
        dataset_entry = IPDataset(
            ip=ip,
            features=features,
            label=0,
            abuse_count=0,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        session.merge(dataset_entry)
    
    session.commit()
    logger.info(f"Dataset construido: {len(malicious_ips)} maliciosas, {len(suspicious_ips)} sospechosas, {len(normal_ips)} normales")
    return session.query(IPDataset).count()

def extract_real_features(ip):
    """Extraer features reales para entrenamiento"""
    abuse_data = fetch_abuse_reports(ip)
    
    # Features numéricas
    features = {
        'abuse_score': abuse_data['abuse_score'] if abuse_data else 0,
        'total_reports': abuse_data['total_reports'] if abuse_data else 0,
        'unique_categories': len(abuse_data['categories']) if abuse_data else 0,
        'has_recent_report': 1 if abuse_data and abuse_data['last_report'] and 
                             datetime.fromisoformat(abuse_data['last_report'].replace('Z', '+00:00')) > 
                             datetime.utcnow() - timedelta(days=7) else 0,
        'is_vpn': 0,  # Lo detectaremos con IPinfo
        'is_proxy': 0,
        'is_tor': 0,
        'is_datacenter': 0
    }
    
    # Obtener datos adicionales de IPinfo
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        data = response.json()
        if 'privacy' in data:
            features['is_vpn'] = 1 if data['privacy'].get('vpn') else 0
            features['is_proxy'] = 1 if data['privacy'].get('proxy') else 0
            features['is_tor'] = 1 if data['privacy'].get('tor') else 0
            features['is_datacenter'] = 1 if data['privacy'].get('hosting') else 0
    except:
        pass
    
    return features
