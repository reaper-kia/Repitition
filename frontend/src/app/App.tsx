import { UserProvider } from '../entities/user/useUser';
import { ErrorBoundary } from '../shared/ui/ErrorBoundary';
import { AppProviders } from './providers/AppProviders';
import { AppRouter } from './router';

export function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <UserProvider>
          <AppRouter />
        </UserProvider>
      </AppProviders>
    </ErrorBoundary>
  );
}
