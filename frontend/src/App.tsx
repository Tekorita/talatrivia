import { AuthProvider } from './context/AuthContext';
import { ActiveTriviaProvider } from './context/ActiveTriviaContext';
import AppRouter from './router/AppRouter';

function App() {
  return (
    <AuthProvider>
      <ActiveTriviaProvider>
        <AppRouter />
      </ActiveTriviaProvider>
    </AuthProvider>
  );
}

export default App;

