import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { joinTrivia, setReady, getLobby, getStatus, updateHeartbeat } from '../../api/player';
import { usePolling } from '../../hooks/usePolling';
import type { LobbyDTO, TriviaStatusDTO } from '../../types/player';

export default function PlayerLobbyPage() {
  const { triviaId } = useParams<{ triviaId: string }>();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [joining, setJoining] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionUnstable, setConnectionUnstable] = useState(false);

  // Join trivia and set ready on mount
  useEffect(() => {
    if (!triviaId || !user) {
      return;
    }

    const initialize = async () => {
      try {
        // Join trivia
        const joinResponse = await joinTrivia(triviaId, user.id);
        if (joinResponse.error) {
          setError(`Failed to join trivia: ${joinResponse.error}`);
          setJoining(false);
          return;
        }

        // Set ready
        const readyResponse = await setReady(triviaId, user.id);
        if (readyResponse.error) {
          // Non-fatal error, continue anyway
          console.warn('Failed to set ready:', readyResponse.error);
        }

        setJoining(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to join trivia');
        setJoining(false);
      }
    };

    initialize();
  }, [triviaId, user]);

  // Poll lobby
  const {
    data: lobbyData,
    error: lobbyError,
    loading: lobbyLoading,
  } = usePolling<LobbyDTO>(
    async () => {
      if (!triviaId) throw new Error('No trivia ID');
      const response = await getLobby(triviaId);
      if (response.error) {
        setConnectionUnstable(true);
        throw new Error(response.error);
      }
      if (!response.data) throw new Error('No lobby data');
      setConnectionUnstable(false);
      return response.data;
    },
    {
      intervalMs: 1000,
      enabled: !joining && !!triviaId,
      onError: () => {
        setConnectionUnstable(true);
      },
    }
  );

  // Poll status and navigate automatically
  const { data: statusData } = usePolling<TriviaStatusDTO>(
    async () => {
      if (!triviaId) throw new Error('No trivia ID');
      const response = await getStatus(triviaId);
      if (response.error) {
        setConnectionUnstable(true);
        throw new Error(response.error);
      }
      if (!response.data) throw new Error('No status data');
      setConnectionUnstable(false);
      return response.data;
    },
    {
      intervalMs: 1000,
      enabled: !joining && !!triviaId,
      onData: (data) => {
        if (data.state === 'IN_PROGRESS') {
          navigate(`/play/trivias/${triviaId}/game`);
        } else if (data.state === 'FINISHED') {
          navigate(`/play/trivias/${triviaId}/results`);
        }
      },
      onError: () => {
        setConnectionUnstable(true);
      },
    }
  );

  // Heartbeat: send every 5 seconds when page is active
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const heartbeatRetryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!triviaId || !user || joining) return;

    const sendHeartbeat = async (retry = false) => {
      try {
        await updateHeartbeat(triviaId, user.id);
        // Success - clear any pending retry
        if (heartbeatRetryRef.current) {
          clearTimeout(heartbeatRetryRef.current);
          heartbeatRetryRef.current = null;
        }
      } catch (error) {
        // Silently fail - heartbeat errors shouldn't break the UI
        console.warn('Heartbeat failed:', error);
        // Retry once after a delay (without spamming)
        if (!retry && !heartbeatRetryRef.current) {
          heartbeatRetryRef.current = setTimeout(() => {
            sendHeartbeat(true);
            heartbeatRetryRef.current = null;
          }, 2000);
        }
      }
    };

    // Send immediately
    sendHeartbeat();

    // Then every 5 seconds
    heartbeatIntervalRef.current = setInterval(() => sendHeartbeat(), 5000);

    // Cleanup on unmount or when dependencies change
    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
      if (heartbeatRetryRef.current) {
        clearTimeout(heartbeatRetryRef.current);
        heartbeatRetryRef.current = null;
      }
    };
  }, [triviaId, user, joining]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (joining) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>Joining Trivia...</h1>
        <p>Please wait...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <h1>Error</h1>
        <div style={{ padding: '1rem', backgroundColor: '#fee', color: '#c33', borderRadius: '4px', marginBottom: '1rem' }}>
          {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
        <button
          onClick={handleLogout}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginLeft: '1rem',
          }}
        >
          Logout
        </button>
      </div>
    );
  }

  const players = lobbyData?.players || [];
  const readyCount = players.filter((p) => p.ready).length;
  const presentCount = players.filter((p) => p.present).length;
  const totalCount = players.length;

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Lobby</h1>
          <p style={{ color: '#666', marginTop: '0.5rem' }}>Esperando que el admin inicie...</p>
        </div>
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

      {connectionUnstable && (
        <div style={{ padding: '0.75rem', backgroundColor: '#fff3cd', color: '#856404', borderRadius: '4px', marginBottom: '1rem', textAlign: 'center' }}>
          ⚠️ Conexión inestable, reintentando…
        </div>
      )}

      {lobbyError !== undefined && !connectionUnstable && (
        <div style={{ padding: '0.75rem', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          Error loading lobby: {lobbyError instanceof Error 
            ? lobbyError.message 
            : typeof lobbyError === 'string' 
              ? lobbyError 
              : 'Unknown error'}
        </div>
      )}

      <div style={{ backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ddd', padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ marginTop: 0 }}>Players</h2>
        <div style={{ marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', gap: '2rem' }}>
          <strong>Presentes: {presentCount} / {totalCount}</strong>
          <strong>Listos: {readyCount} / {totalCount}</strong>
        </div>

        {lobbyLoading && !lobbyData ? (
          <div>Loading players...</div>
        ) : players.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>No players yet</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {players.map((player) => (
              <div
                key={player.user_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem',
                  backgroundColor: player.user_id === user?.id ? '#e7f3ff' : '#f5f5f5',
                  borderRadius: '4px',
                  border: player.user_id === user?.id ? '2px solid #007bff' : '1px solid #ddd',
                }}
              >
                <span style={{ fontWeight: player.user_id === user?.id ? 'bold' : 'normal' }}>
                  {player.name} {player.user_id === user?.id && '(You)'}
                </span>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <span
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.875rem',
                      backgroundColor: player.present ? '#28a745' : '#ffc107',
                      color: 'white',
                      fontWeight: 'bold',
                    }}
                  >
                    {player.present ? '✅ Presente' : '⏳ Esperando'}
                  </span>
                  <span
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.875rem',
                      backgroundColor: player.ready ? '#28a745' : '#ffc107',
                      color: 'white',
                      fontWeight: 'bold',
                    }}
                  >
                    {player.ready ? '✅ Ready' : '⏳ Not ready'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {statusData && (
        <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '4px', textAlign: 'center' }}>
          <p style={{ margin: 0, color: '#666' }}>
            Status: <strong>{statusData.state}</strong>
            {statusData.current_question_index !== undefined && (
              <> | Question: {statusData.current_question_index + 1}</>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
