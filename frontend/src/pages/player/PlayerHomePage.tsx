import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getAssignedTrivias } from '../../api/player';
import type { AssignedTrivia } from '../../api/player';

export default function PlayerHomePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [trivias, setTrivias] = useState<AssignedTrivia[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }

    const loadTrivias = async () => {
      setLoading(true);
      setError(null);
      const response = await getAssignedTrivias(user.id);
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setTrivias(response.data);
      }
      setLoading(false);
    };

    loadTrivias();
  }, [user]);

  const handleEnterTrivia = (trivia: AssignedTrivia) => {
    // Navigate intelligently based on status
    if (trivia.status === 'LOBBY' || trivia.status === 'DRAFT') {
      navigate(`/play/trivias/${trivia.trivia_id}/lobby`);
    } else if (trivia.status === 'IN_PROGRESS') {
      navigate(`/play/trivias/${trivia.trivia_id}/game`);
    } else if (trivia.status === 'FINISHED') {
      navigate(`/play/trivias/${trivia.trivia_id}/results`);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'LOBBY':
      case 'DRAFT':
        return { backgroundColor: '#ffc107', color: '#856404' };
      case 'IN_PROGRESS':
        return { backgroundColor: '#007bff', color: '#fff' };
      case 'FINISHED':
        return { backgroundColor: '#28a745', color: '#fff' };
      default:
        return { backgroundColor: '#6c757d', color: '#fff' };
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'Borrador';
      case 'LOBBY':
        return 'Lobby';
      case 'IN_PROGRESS':
        return 'En Progreso';
      case 'FINISHED':
        return 'Finalizada';
      default:
        return status;
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Mis Trivias</h1>
        <button
          onClick={handleLogout}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Logout
        </button>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          Error loading trivias: {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>Loading trivias...</div>
      ) : trivias.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No tienes trivias asignadas.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {trivias.map((trivia) => {
            const badgeStyle = getStatusBadgeColor(trivia.status);
            return (
              <div
                key={trivia.trivia_id}
                style={{
                  backgroundColor: '#fff',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                }}
              >
                <div>
                  <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>{trivia.title}</h2>
                  <p style={{ color: '#666', marginBottom: '0.5rem' }}>{trivia.description}</p>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      ...badgeStyle,
                    }}
                  >
                    {getStatusLabel(trivia.status)}
                  </span>
                </div>
                <button
                  onClick={() => handleEnterTrivia(trivia)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    fontSize: '1rem',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                  }}
                >
                  Entrar
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
