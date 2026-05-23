import { useState } from 'react';
import MapComponent from './MapComponent';

function App() {
  const [ip, setIp] = useState('');
  const [result, setResult] = useState(null);

  const analyzeIP = async () => {
    const res = await fetch('http://localhost:8000/api/v1/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    const data = await res.json();
    setResult(data);
  };

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold">🌐 NeoTrace AI</h1>
      <input 
        value={ip} onChange={(e) => setIp(e.target.value)} 
        placeholder="Ej: 8.8.8.8" className="border p-2 m-2"
      />
      <button onClick={analyzeIP} className="bg-blue-500 text-white p-2">
        Analizar con IA
      </button>
      
      {result && (
        <div className="mt-4">
          <h2>📍 {result.location.city}, {result.location.country}</h2>
          <p>🤖 Score riesgo: {result.risk_score}/100</p>
          <p>💡 Insight IA: {result.ai_insight}</p>
          <MapComponent lat={result.location.loc?.split(',')[0]} lng={result.location.loc?.split(',')[1]} />
        </div>
      )}
    </div>
  );
}
