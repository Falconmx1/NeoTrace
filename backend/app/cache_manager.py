from database import redis_client
import json
import hashlib
from datetime import datetime, timedelta

class NeoTraceCache:
    def __init__(self, ttl_minutes=60):
        self.ttl = ttl_minutes * 60
    
    def _get_key(self, ip):
        return f"neotrace:{ip}"
    
    def get_cached_result(self, ip):
        """Obtener resultado cachead"""
        key = self._get_key(ip)
        cached = redis_client.get(key)
        if cached:
            data = json.loads(cached)
            # Actualizar último acceso
            redis_client.hset(f"stats:{ip}", "last_access", datetime.now().isoformat())
            return data
        return None
    
    def cache_result(self, ip, analysis_result):
        """Cachear resultado"""
        key = self._get_key(ip)
        redis_client.setex(key, self.ttl, json.dumps(analysis_result))
        
        # Guardar estadísticas
        redis_client.hset(f"stats:{ip}", "first_cached", datetime.now().isoformat())
        redis_client.hset(f"stats:{ip}", "access_count", 
                         redis_client.hincrby(f"stats:{ip}", "access_count", 1))
    
    def get_hot_ips(self, limit=100):
        """Obtener IPs más consultadas"""
        keys = redis_client.keys("stats:*")
        hot_ips = []
        for key in keys:
            ip = key.split(":")[1]
            access_count = redis_client.hget(key, "access_count")
            if access_count:
                hot_ips.append((ip, int(access_count)))
        
        hot_ips.sort(key=lambda x: x[1], reverse=True)
        return hot_ips[:limit]
    
    def preload_common_ips(self):
        """Precargar IPs comunes en caché"""
        common_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222', '31.13.79.246', '142.250.185.46']
        for ip in common_ips:
            if not self.get_cached_result(ip):
                # Análisis asíncrono en background
                from ai_engine import analyze_ip_with_ai
                result = analyze_ip_with_ai(ip, {})
                self.cache_result(ip, result)

cache_system = NeoTraceCache()
