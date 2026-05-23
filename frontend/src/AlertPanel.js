import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

function AlertPanel() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({ high: 0, medium: 0, low: 0 });
  
  useEffect(() => {
    // WebSocket para alertas en tiempo real
    const ws = new WebSocket('ws://localhost:8000/ws/alerts');
    
    ws.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      setAlerts(prev => [alert, ...prev].slice(0, 50)); // Últimas 50
      
      // Actualizar estadísticas
      setStats(prev => ({
        ...prev,
        [alert.severity]: prev[alert.severity] + 1
      }));
      
      // Notificación del navegador
      if (Notification.permission === 'granted') {
        new Notification(`NeoTrace Alert: ${alert.type}`, {
          body: alert.message.substring(0, 100),
          icon: '/alert-icon.png'
        });
      }
    };
    
    return () => ws.close();
  }, []);
  
  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-orange-600';
      case 'medium': return 'bg-yellow-600';
      default: return 'bg-blue-600';
    }
  };
  
  const getSeverityIcon = (severity) => {
    switch(severity) {
      case 'critical': return <XCircle className="text-red-500" />;
      case 'high': return <AlertTriangle className="text-orange-500" />;
      case 'medium': return <Bell className="text-yellow-500" />;
      default: return <CheckCircle className="text-blue-500" />;
    }
  };
  
  return (
    <div className="p-4 bg-gray-900 text-white min-h-screen">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">🚨 Centro de Alertas</h1>
        
        {/* Estadísticas */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-red-900 p-4 rounded-lg">
            <div className="text-2xl font-bold">{stats.high}</div>
            <div className="text-sm">Alertas Críticas</div>
          </div>
          <div className="bg-yellow-900 p-4 rounded-lg">
            <div className="text-2xl font-bold">{stats.medium}</div>
            <div className="text-sm">Alertas Medias</div>
          </div>
          <div className="bg-blue-900 p-4 rounded-lg">
            <div className="text-2xl font-bold">{stats.low}</div>
            <div className="text-sm">Alertas Bajas</div>
          </div>
        </div>
      </div>
      
      {/* Lista de alertas */}
      <div className="space-y-3">
        {alerts.map((alert, idx) => (
          <div key={idx} className={`${getSeverityColor(alert.severity)} bg-opacity-20 p-4 rounded-lg border-l-4 ${getSeverityColor(alert.severity)}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                {getSeverityIcon(alert.severity)}
                <div>
                  <div className="font-bold">{alert.type.replace('_', ' ').toUpperCase()}</div>
                  <div className="text-sm text-gray-300">{alert.timestamp}</div>
                </div>
              </div>
              <button className="text-gray-400 hover:text-white">✓ Marcar como leída</button>
            </div>
            <div className="mt-2 text-sm whitespace-pre-wrap">{alert.message}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AlertPanel;
