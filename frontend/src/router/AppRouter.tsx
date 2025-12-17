import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomeRedirect from '../pages/HomeRedirect';
import LoginPage from '../pages/LoginPage';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage';
import PlayerLobbyPage from '../pages/player/PlayerLobbyPage';
import ProtectedRoute from './ProtectedRoute';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="ADMIN">
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/player/lobby"
          element={
            <ProtectedRoute requiredRole="PLAYER">
              <PlayerLobbyPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

