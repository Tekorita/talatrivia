import { useState } from 'react';
import { get } from '../api/api';

export default function Home() {
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const checkApiStatus = async () => {
    setLoading(true);
    setStatus('');

    const response = await get<{ status: string }>('/health');

    if (response.error) {
      setStatus(`Error: ${response.error}`);
    } else if (response.data) {
      setStatus('Backend connected ✓');
    } else {
      setStatus('Unexpected response from backend');
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>TalaTrivia Frontend</h1>
      <button
        onClick={checkApiStatus}
        disabled={loading}
        style={{
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
          marginTop: '1rem',
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Checking...' : 'Check API status'}
      </button>
      {status && (
        <p style={{ marginTop: '1rem', color: status.includes('Error') ? 'red' : 'green' }}>
          {status}
        </p>
      )}
    </div>
  );
}

