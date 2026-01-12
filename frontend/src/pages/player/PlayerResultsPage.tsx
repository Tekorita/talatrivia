import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getRanking } from '../../api/player';
import { useTriviaEvents } from '../../hooks/useTriviaEvents';
import type { RankingRowDTO } from '../../types/player';

export default function PlayerResultsPage() {
  const { triviaId } = useParams<{ triviaId: string }>();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [rankingData, setRankingData] = useState<RankingRowDTO[]>([]);
  const [rankingError, setRankingError] = useState<unknown>(undefined);
  const [rankingLoading, setRankingLoading] = useState(true);

  const goToLobby = () => {
    navigate('/play');
  };

  // Load initial ranking
  useEffect(() => {
    const loadInitialRanking = async () => {
      if (!triviaId) return;
      try {
        const response = await getRanking(triviaId);
        if (response.error) {
          setRankingError(new Error(response.error));
          setRankingLoading(false);
        } else if (response.data) {
          setRankingData(response.data);
          setRankingLoading(false);
          setRankingError(undefined);
        }
      } catch (err) {
        setRankingError(err);
        setRankingLoading(false);
      }
    };
    loadInitialRanking();
  }, [triviaId]);

  // Use SSE events instead of polling for updates
  useTriviaEvents({
    triviaId: triviaId || '',
    userId: user?.id,
    role: 'PLAYER',
    enabled: !!triviaId,
    onRankingUpdated: (data) => {
      // Map SSE ranking format to RankingRowDTO[] format
      setRankingData(
        data.entries.map((entry) => ({
          user_id: entry.user_id,
          name: entry.name,
          score: entry.score,
          position: entry.position,
        }))
      );
      setRankingLoading(false);
      setRankingError(undefined);
    },
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="container py-4" style={{ maxWidth: 900 }}>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1 text-dark">Resultados</h1>
          <p className="text-muted mb-0">Revisa tu posición en el ranking.</p>
        </div>
        <div className="d-flex gap-2">
          <button onClick={goToLobby} className="btn btn-primary btn-animated">
            Regresar al lobby
          </button>
          <button onClick={handleLogout} className="btn btn-outline-danger btn-animated">
            Cerrar sesión
          </button>
        </div>
      </div>

      {rankingError !== undefined && (
        <div className="alert alert-warning">
          Error al cargar el ranking:{' '}
          {rankingError instanceof Error
            ? rankingError.message
            : typeof rankingError === 'string'
              ? rankingError
              : 'Error desconocido'}
        </div>
      )}

      {rankingLoading && !rankingData ? (
        <div className="text-center py-4">Cargando ranking...</div>
      ) : rankingData && rankingData.length > 0 ? (
        <div className="card fade-in">
          <div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Posición</th>
                  <th>Nombre</th>
                  <th className="text-end">Puntaje</th>
                </tr>
              </thead>
              <tbody>
                {rankingData.map((entry, index) => {
                  const isCurrentUser = entry.user_id === user?.id;
                  return (
                    <tr
                      key={entry.user_id}
                      className={isCurrentUser ? 'table-primary' : ''}
                      style={{ fontWeight: isCurrentUser ? 'bold' : 'normal' }}
                    >
                      <td>{entry.position !== undefined ? entry.position : index + 1}</td>
                      <td>
                        {entry.name} {isCurrentUser && <span className="text-primary">(Tú)</span>}
                      </td>
                      <td className="text-end">{entry.score}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center text-muted py-4">No hay datos de ranking</div>
      )}
    </div>
  );
}
