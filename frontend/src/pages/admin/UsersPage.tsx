import { useState, useEffect, FormEvent } from 'react';
import { getUsers, createUser } from '../../api/usersApi';
import { User } from '../../types';

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'ADMIN' | 'PLAYER'>('PLAYER');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    const response = await getUsers();
    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setError('El endpoint aún no está disponible');
      } else {
        setError(response.error);
      }
    } else if (response.data) {
      setUsers(response.data);
    }
    setLoading(false);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);

    const response = await createUser({
      name: name.trim(),
      email: email.trim(),
      password,
      role,
    });

    if (response.error) {
      if (response.error.includes('404') || response.error.includes('not found')) {
        setCreateError('El endpoint aún no está disponible');
      } else {
        setCreateError(response.error);
      }
    } else if (response.data) {
      // Reset form
      setName('');
      setEmail('');
      setPassword('');
      setRole('PLAYER');
      setShowForm(false);
      // Reload users
      loadUsers();
    }
    setCreateLoading(false);
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="fw-bold mb-1">Usuarios</h2>
          <p className="text-muted mb-0">Administra los usuarios del sistema.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary btn-animated"
        >
          {showForm ? 'Cancelar' : 'Crear usuario'}
        </button>
      </div>

      {showForm && (
        <div className="card mb-4 fade-in">
          <div className="card-body">
            <h5 className="card-title mb-3">Crear usuario</h5>
            {createError && (
              <div className="alert alert-danger">{createError}</div>
            )}
            <form onSubmit={handleSubmit} className="row g-3">
              <div className="col-md-6">
                <label className="form-label">Nombre *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  disabled={createLoading}
                  className="form-control"
                  placeholder="Nombre completo"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Email *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={createLoading}
                  className="form-control"
                  placeholder="email@ejemplo.com"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Contraseña *</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={createLoading}
                  className="form-control"
                  placeholder="Contraseña"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Rol</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as 'ADMIN' | 'PLAYER')}
                  disabled={createLoading}
                  className="form-select"
                >
                  <option value="PLAYER">Jugador</option>
                  <option value="ADMIN">Administrador</option>
                </select>
              </div>
              <div className="col-12 d-flex justify-content-end">
                <button
                  type="submit"
                  disabled={createLoading}
                  className="btn btn-success btn-animated"
                >
                  {createLoading ? 'Creando...' : 'Crear usuario'}
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
      ) : users.length === 0 && !error ? (
        <div className="text-center text-muted py-5">No hay usuarios creados</div>
      ) : (
        <div className="card fade-in">
          <div className="table-responsive">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Email</th>
                  <th>Rol</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.name}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className="badge bg-light text-dark">
                        {user.role === 'ADMIN' ? 'Administrador' : 'Jugador'}
                      </span>
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
