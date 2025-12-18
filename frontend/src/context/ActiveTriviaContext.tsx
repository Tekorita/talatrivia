import { createContext, useContext, useState, ReactNode } from 'react';

interface ActiveTriviaContextType {
  activeTriviaId: string | null;
  setActiveTriviaId: (id: string | null) => void;
}

const ActiveTriviaContext = createContext<ActiveTriviaContextType | undefined>(undefined);

export function ActiveTriviaProvider({ children }: { children: ReactNode }) {
  const [activeTriviaId, setActiveTriviaId] = useState<string | null>(null);

  return (
    <ActiveTriviaContext.Provider value={{ activeTriviaId, setActiveTriviaId }}>
      {children}
    </ActiveTriviaContext.Provider>
  );
}

export function useActiveTrivia() {
  const context = useContext(ActiveTriviaContext);
  if (context === undefined) {
    throw new Error('useActiveTrivia must be used within an ActiveTriviaProvider');
  }
  return context;
}
