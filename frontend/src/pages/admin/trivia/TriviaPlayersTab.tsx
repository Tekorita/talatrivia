import { useState, useEffect } from 'react';
import { getUsers } from '../../../api/usersApi';
import { listTriviaPlayers, addPlayerToTrivia } from '../../../api/triviasApi';
import { User } from '../../../types';

interface TriviaPlayersTabProps {
  triviaId: string;
}

export default function TriviaPlayersTab({ triviaId }: TriviaPlayersTabProps) {
  const [assignedPlayers, setAssignedPlayers] = useState<User[]>([]);
  const [availablePlayers, setAvailablePlayers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addLoading, setAddLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  useEffect(() => {
    loadAssignedPlayers();
    loadAvailablePlayers();
  }, [triviaId]);

  const loadAssignedPlayers = async () => {
    setLoading(true);
    setError(null);
    const response = await listTriviaPlayers(triviaId);
    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setError('El endpoint de lista de jugadores aún no está disponible');
      } else {
        setError(response.error);
      }
    } else if (response.data) {
      setAssignedPlayers(response.data);
    }
    setLoading(false);
  };

  const loadAvailablePlayers = async () => {
    const response = await getUsers();
    if (response.data) {
      // Filter only PLAYER users that are not already assigned
      const playerUsers = response.data.filter((u) => u.role === 'PLAYER');
      const assignedIds = new Set(assignedPlayers.map((p) => p.id));
      setAvailablePlayers(playerUsers.filter((u) => !assignedIds.has(u.id)));
    }
  };

  const handleAddPlayer = async (userId: string) => {
    setAddLoading(true);
    setAddError(null);
    const response = await addPlayerToTrivia(triviaId, userId);
    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setAddError('El endpoint de asociación aún no está disponible');
      } else {
        setAddError(response.error);
      }
    } else {
      // Reload lists
      await loadAssignedPlayers();
      await loadAvailablePlayers();
    }
    setAddLoading(false);
  };

  // Reload available players when assigned players change
  useEffect(() => {
    loadAvailablePlayers();
  }, [assignedPlayers.length]);

  return (
    <div>
      <h4 className="mb-4">Jugadores</h4>

      {addError && (
        <div className="alert alert-danger mb-3">{addError}</div>
      )}

      <div className="row g-4">
        {/* Assigned Players */}
        <div className="col-md-6">
          <h5 className="mb-3">Jugadores asignados</h5>
          {error && (
            <div className="alert alert-warning mb-3">{error}</div>
          )}
          {loading ? (
            <div className="text-center py-4">Cargando...</div>
          ) : assignedPlayers.length === 0 && !error ? (
            <div className="text-center text-muted py-5">No hay jugadores asignados</div>
          ) : (
            <div className="card fade-in">
              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Email</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignedPlayers.map((player) => (
                      <tr key={player.id}>
                        <td>{player.name}</td>
                        <td>{player.email}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Available Players */}
        <div className="col-md-6">
          <h5 className="mb-3">Jugadores disponibles</h5>
          {availablePlayers.length === 0 ? (
            <div className="text-center text-muted py-5">No hay jugadores disponibles</div>
          ) : (
            <div className="card fade-in">
              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Email</th>
                      <th>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {availablePlayers.map((player) => (
                      <tr key={player.id}>
                        <td>{player.name}</td>
                        <td>{player.email}</td>
                        <td>
                          <button
                            onClick={() => handleAddPlayer(player.id)}
                            disabled={addLoading}
                            className="btn btn-success btn-sm btn-animated"
                          >
                            Agregar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
