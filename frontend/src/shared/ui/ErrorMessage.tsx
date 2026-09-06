import { CircleAlert } from 'lucide-react';
import { Button } from './Button';

export function ErrorMessage({ message, onRetry, retryLabel = 'Повторить' }: { message: string; onRetry?: () => void; retryLabel?: string }) {
  return (
    <div className="error-state" role="alert">
      <CircleAlert size={22} />
      <div><strong>Не удалось выполнить запрос</strong><p>{message}</p></div>
      {onRetry && <Button type="button" variant="secondary" onClick={onRetry}>{retryLabel}</Button>}
    </div>
  );
}
