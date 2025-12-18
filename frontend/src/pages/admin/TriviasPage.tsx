import { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTrivias, createTrivia, resetTrivia } from '../../api/triviasApi';
import { getUsers } from '../../api/usersApi';
import { Trivia, User } from '../../types';

export default function TriviasPage() {
  const navigate = useNavigate();
  const [trivias, setTrivias] = useState<Trivia[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [resettingId, setResettingId] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  useEffect(() => {
    loadTrivias();
    loadUsers();
  }, []);

  const loadTrivias = async () => {
    setLoading(true);
    setError(null);
    const response = await getTrivias();
    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setError('El endpoint aún no está disponible');
      } else {
        setError(response.error);
      }
    } else if (response.data) {
      setTrivias(response.data);
    }
    setLoading(false);
  };

  const loadUsers = async () => {
    const response = await getUsers();
    if (response.data) {
      // Filter only PLAYER users
      setUsers(response.data.filter((u) => u.role === 'PLAYER'));
    }
  };

  const handleUserToggle = (userId: string) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleReset = async (triviaId: string) => {
    setResettingId(triviaId);
    const response = await resetTrivia(triviaId);
    if (response.error) {
      alert(`Failed to reset trivia: ${response.error}`);
    } else {
      loadTrivias();
    }
    setResettingId(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (selectedUserIds.length === 0) {
      setCreateError('Selecciona al menos un jugador');
      return;
    }

    setCreateLoading(true);
    setCreateError(null);

    const response = await createTrivia({
      title: title.trim(),
      description: description.trim(),
      user_ids: selectedUserIds,
      question_ids: [], // Questions are added from Trivia Detail
    });

    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setCreateError('El endpoint aún no está disponible');
      } else if (response.error.includes('422') || response.error.includes('question_ids')) {
        setCreateError('El backend requiere question_ids. Agrega preguntas desde el detalle de la trivia.');
      } else {
        setCreateError(response.error);
      }
    } else if (response.data) {
      // Reset form
      setTitle('');
      setDescription('');
      setSelectedUserIds([]);
      setShowForm(false);
      // Reload trivias
      loadTrivias();
      // Navigate to trivia detail
      navigate(`/admin/trivias/${response.data.id}`);
    }
    setCreateLoading(false);
  };

  return (
    <div className="container-fluid">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="fw-bold mb-1">Trivias</h2>
          <p className="text-muted mb-0">Administra, reinicia y crea trivias.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary btn-animated"
        >
          {showForm ? 'Cancelar' : 'Crear trivia'}
        </button>
      </div>

      {showForm && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <h5 className="card-title mb-3">Crear trivia</h5>
            {createError && (
              <div className="alert alert-danger">{createError}</div>
            )}
            <form onSubmit={handleSubmit} className="row g-3">
              <div className="col-md-6">
                <label className="form-label">Título *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  disabled={createLoading}
                  className="form-control"
                  placeholder="Ej: Trivia general"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Descripción *</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  disabled={createLoading}
                  rows={2}
                  className="form-control"
                  placeholder="Añade un breve detalle"
                />
              </div>
              <div className="col-12">
                <label className="form-label">Selecciona jugadores *</label>
                <div className="border rounded p-2" style={{ maxHeight: 180, overflowY: 'auto' }}>
                  {users.length === 0 ? (
                    <div className="text-muted">No hay jugadores disponibles</div>
                  ) : (
                    users.map((user) => (
                      <label key={user.id} className="d-flex align-items-center gap-2 py-1">
                        <input
                          type="checkbox"
                          checked={selectedUserIds.includes(user.id)}
                          onChange={() => handleUserToggle(user.id)}
                          disabled={createLoading}
                          className="form-check-input"
                        />
                        <span>{user.name} ({user.email})</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
              <div className="col-12 d-flex justify-content-end">
                <button
                  type="submit"
                  disabled={createLoading || selectedUserIds.length === 0}
                  className="btn btn-success btn-animated"
                >
                  {createLoading ? 'Creando...' : 'Crear trivia'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-warning">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-4">Cargando...</div>
      ) : trivias.length === 0 && !error ? (
        <div className="text-center text-muted py-5">No hay trivias creadas</div>
      ) : (
        <div className="card fade-in">
          <div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Estado</th>
                  <th>Índice de pregunta</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {trivias.map((trivia) => (
                  <tr key={trivia.id}>
                    <td className="fw-semibold">{trivia.title}</td>
                    <td><span className="badge bg-light text-dark">{trivia.status}</span></td>
                    <td>{trivia.current_question_index}</td>
                    <td className="d-flex gap-2">
                      <button
                        onClick={() => navigate(`/admin/trivias/${trivia.id}`)}
                        className="btn btn-primary btn-sm btn-animated"
                      >
                        Abrir
                      </button>
                      <button
                        onClick={() => handleReset(trivia.id)}
                        disabled={resettingId === trivia.id}
                        className={`btn btn-sm btn-animated ${resettingId === trivia.id ? 'btn-secondary' : 'btn-danger'}`}
                      >
                        {resettingId === trivia.id ? 'Reiniciando...' : 'Reiniciar'}
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
  );
}
