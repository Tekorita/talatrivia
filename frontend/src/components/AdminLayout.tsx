import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/admin/users', label: 'Usuarios' },
    { path: '/admin/trivias', label: 'Trivias' },
    { path: '/admin/control', label: 'Control (En vivo)' },
  ];

  return (
    <div className="d-flex min-vh-100">
      {/* Sidebar */}
      <aside className="bg-white shadow-sm px-3 py-4" style={{ width: 230 }}>
        <h2 className="fw-bold mb-4 text-primary">Panel Admin</h2>
        <nav className="d-flex flex-column gap-2">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 sidebar-link ${active ? 'active' : ''} text-decoration-none text-dark`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-grow-1 d-flex flex-column">
        {/* Header */}
        <header className="d-flex justify-content-between align-items-center bg-white px-4 py-3 shadow-sm">
          <h1 className="h4 mb-0 fw-bold text-dark">Panel de administración</h1>
          <div className="d-flex align-items-center gap-3">
            <div className="text-end">
              <div className="fw-semibold">{user?.name}</div>
              <div className="text-muted small">{user?.email}</div>
            </div>
            <button className="btn btn-outline-danger btn-sm btn-animated" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-grow-1 p-4">
          <div className="fade-in">{children}</div>
        </main>
      </div>
    </div>
  );
}
