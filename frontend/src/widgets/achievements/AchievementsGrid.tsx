import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { EmptyState } from '../../shared/ui/EmptyState';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

export function AchievementsGrid() {
  const { data, loading, error, reload } = useAsync(() => api.getAchievements(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data || data.length === 0) {
    return <EmptyState title="Достижений пока нет" message="Выполняйте задания, чтобы открыть награды." />;
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 16 }}>
      {data.map((a) => (
        <div
          key={a.code}
          data-earned={a.earned ? 'true' : 'false'}
          style={{
            padding: 16,
            borderRadius: 12,
            textAlign: 'center',
            border: a.earned ? '1px solid var(--color-primary, #b5502a)' : '1px dashed var(--color-border, #ccc)',
            opacity: a.earned ? 1 : 0.55,
          }}
        >
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>{a.icon}</div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{a.title}</div>
          {a.earned && a.achieved_at ? (
            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>
              получено {new Date(a.achieved_at).toLocaleDateString('ru-RU')}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
