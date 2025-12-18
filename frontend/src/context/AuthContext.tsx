import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { setUnauthorizedHandler } from '../api/api';

export type UserRole = 'ADMIN' | 'PLAYER';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

interface AuthContextType {
  user: User | null;
  login: (user: User) => void;
  logout: () => void;
  showSnackbar: (message: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Generate a unique tab ID on first load
const getTabId = (): string => {
  // Use localStorage to persist tab ID across refreshes, but unique per tab
  const stored = localStorage.getItem('talatrivia_tab_id');
  if (stored) {
    return stored;
  }
  const tabId = `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('talatrivia_tab_id', tabId);
  return tabId;
};

const getStorageKey = (): string => {
  const tabId = getTabId();
  return `talatrivia_session_${tabId}`;
};

// Load user from storage synchronously (before first render)
const loadUserFromStorage = (): User | null => {
  try {
    const storageKey = getStorageKey();
    const storedSession = localStorage.getItem(storageKey);
    if (storedSession) {
      return JSON.parse(storedSession) as User;
    }
  } catch (error) {
    console.error('Error parsing stored session:', error);
    const storageKey = getStorageKey();
    localStorage.removeItem(storageKey);
  }
  return null;
};

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize user from storage synchronously to prevent redirect on refresh
  const [user, setUser] = useState<User | null>(loadUserFromStorage);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  const [showSnackbar, setShowSnackbar] = useState(false);

  const login = (user: User) => {
    setUser(user);
    const storageKey = getStorageKey();
    localStorage.setItem(storageKey, JSON.stringify(user));
  };

  const logout = () => {
    setUser(null);
    const storageKey = getStorageKey();
    localStorage.removeItem(storageKey);
  };

  const showSnackbarMessage = (message: string) => {
    setSnackbarMessage(message);
    setShowSnackbar(true);
    // Auto-hide after 5 seconds
    setTimeout(() => {
      setShowSnackbar(false);
    }, 5000);
  };

  // Configure 401 handler
  useEffect(() => {
    const handler = () => {
      showSnackbarMessage('Sesión expirada, inicia sesión nuevamente');
      logout();
      // Navigate to login will be handled by ProtectedRoute
    };
    setUnauthorizedHandler(handler);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, showSnackbar: showSnackbarMessage }}>
      {children}
      {showSnackbar && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#333',
            color: '#fff',
            padding: '1rem 1.5rem',
            borderRadius: '4px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            zIndex: 10000,
            maxWidth: '90%',
            textAlign: 'center',
          }}
        >
          {snackbarMessage}
        </div>
      )}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
