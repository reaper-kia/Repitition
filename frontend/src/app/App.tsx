import { AppProviders } from './providers/AppProviders';
import { AppRouter } from './router';
import { ErrorBoundary } from '../shared/ui/ErrorBoundary';

export function App() {
  return (
    <ErrorBoundary>
      <AppProviders><AppRouter /></AppProviders>
    </ErrorBoundary>
  );
}
