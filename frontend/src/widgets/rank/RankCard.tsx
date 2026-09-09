import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

export function RankCard() {
  const { data, loading, error, reload } = useAsync(() => api.getRank(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data) return null;

  const isMax = data.visits_to_next === null;
  const percent = isMax ? 100 : Math.round((data.visits_total / (data.visits_total + (data.visits_to_next ?? 0))) * 100);

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>{data.title}</h2>
        <span style={{ fontSize: '1.4rem', fontWeight: 600 }}>{data.visits_total} визитов</span>
      </div>
      {isMax ? (
        <p style={{ margin: 0, fontWeight: 600 }}>🏆 Максимальный уровень</p>
      ) : (
        <>
          <p style={{ opacity: 0.75, marginBottom: 12 }}>
            до «{data.next_title}» ещё {data.visits_to_next}
          </p>
          <div style={{ height: 12, borderRadius: 6, background: 'var(--color-border, #ddd)', overflow: 'hidden' }}>
            <div style={{ width: percent + '%', height: '100%', background: 'var(--color-primary, #b5502a)' }} />
          </div>
        </>
      )}
    </div>
  );
}
