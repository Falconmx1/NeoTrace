import { useEffect, useState } from 'react';

function RealtimeScanner() {
  const [ws, setWs] = useState(null);
  const [ipsFound, setIpsFound] = useState([]);
  const [scanning, setScanning] = useState(false);
  
  const startScan = () => {
    const websocket = new WebSocket('ws://localhost:8000/ws/scan');
    
    websocket.onopen = () => {
      websocket.send(JSON.stringify({
        command: 'scan_network',
        network: '8.8.8.0/24'  // Ejemplo, puedes cambiarlo
      }));
      setScanning(true);
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'ip_found') {
        setIpsFound(prev => [...prev, { 
          ip: data.ip, 
          hostname: data.hostname,
          timestamp: new Date() 
        }]);
      } else if (data.type === 'analysis') {
        console.log('Análisis IA:', data.result);
      }
    };
    
    setWs(websocket);
  };
  
  return (
    <div className="p-4">
      <button 
        onClick={startScan}
        disabled={scanning}
        className="bg-red-500 text-white p-2 rounded"
      >
        {scanning ? 'Escaneando...' : 'Iniciar Escaneo en Tiempo Real'}
      </button>
      
      <div className="mt-4">
        <h3>IPs Encontradas ({ipsFound.length})</h3>
        <ul>
          {ipsFound.map((item, idx) => (
            <li key={idx}>
              {item.ip} - {item.hostname || 'sin hostname'} - {item.timestamp.toLocaleTimeString()}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
