import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

export function ChallengeCard() {
  const { data, loading, error, reload } = useAsync(() => api.getChallenge(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data) return null;

  if (data.status !== 'IN_PROGRESS') {
    return (
      <div className="card" style={{ padding: 24, textAlign: 'center' }}>
        <strong>Программа завершена</strong>
      </div>
    );
  }

  const percent = Math.round((data.visits_in_stage / data.required_visits) * 100);

  return (
    <div className="card" style={{ padding: 24 }}>
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>Онбординг</h3>
      <p style={{ opacity: 0.75, marginBottom: 12 }}>
        Этап {data.current_stage} из {data.total_stages} · {data.visits_in_stage} из {data.required_visits} визитов
      </p>
      <div style={{ height: 12, borderRadius: 6, background: 'var(--color-border, #ddd)', overflow: 'hidden' }}>
        <div style={{ width: percent + '%', height: '100%', background: 'var(--color-primary, #b5502a)' }} />
      </div>
    </div>
  );
}
