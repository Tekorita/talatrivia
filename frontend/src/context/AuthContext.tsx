import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'talatrivia_session';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Cargar sesión desde localStorage al montar
  useEffect(() => {
    const storedSession = localStorage.getItem(STORAGE_KEY);
    if (storedSession) {
      try {
        const parsedUser = JSON.parse(storedSession) as User;
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing stored session:', error);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  const login = (user: User) => {
    setUser(user);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
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
