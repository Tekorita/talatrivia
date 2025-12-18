import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomeRedirect from '../pages/HomeRedirect';
import LoginPage from '../pages/LoginPage';
import AdminLayout from '../components/AdminLayout';
import UsersPage from '../pages/admin/UsersPage';
import TriviasPage from '../pages/admin/TriviasPage';
import TriviaDetailPage from '../pages/admin/TriviaDetailPage';
import ControlPage from '../pages/admin/ControlPage';
import PlayerHomePage from '../pages/player/PlayerHomePage';
import PlayerLobbyPage from '../pages/player/PlayerLobbyPage';
import PlayerGamePage from '../pages/player/PlayerGamePage';
import PlayerResultsPage from '../pages/player/PlayerResultsPage';
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
              <Navigate to="/admin/users" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute requiredRole="ADMIN">
              <AdminLayout>
                <Routes>
                  <Route path="users" element={<UsersPage />} />
                  <Route path="trivias" element={<TriviasPage />} />
                  <Route path="trivias/:triviaId" element={<TriviaDetailPage />} />
                  <Route path="control" element={<ControlPage />} />
                  <Route path="*" element={<Navigate to="/admin/users" replace />} />
                </Routes>
              </AdminLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/play"
          element={
            <ProtectedRoute requiredRole="PLAYER">
              <PlayerHomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/play/trivias/:triviaId/lobby"
          element={
            <ProtectedRoute requiredRole="PLAYER">
              <PlayerLobbyPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/play/trivias/:triviaId/game"
          element={
            <ProtectedRoute requiredRole="PLAYER">
              <PlayerGamePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/play/trivias/:triviaId/results"
          element={
            <ProtectedRoute requiredRole="PLAYER">
              <PlayerResultsPage />
            </ProtectedRoute>
          }
        />
        {/* Legacy route for backward compatibility */}
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

