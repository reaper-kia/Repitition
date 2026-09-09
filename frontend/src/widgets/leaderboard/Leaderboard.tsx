import { useState } from 'react';
import { useUser } from '../../entities/user/useUser';
import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { Button } from '../../shared/ui/Button';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

const CLUB_ID = 'club1';
const WEEKS = ['2025-W35', '2025-W36'];

export function Leaderboard() {
  const { user } = useUser();
  const [week, setWeek] = useState('2025-W36');
  const { data, loading, error, reload } = useAsync(() => api.getLeaderboard(CLUB_ID, week), [week]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data) return null;

  return (
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>Рейтинг недели {data.week}</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          {WEEKS.map((w) => (
            <Button key={w} variant={w === week ? 'primary' : 'secondary'} onClick={() => setWeek(w)}>
              {w === '2025-W36' ? 'Текущая' : 'Прошлая'}
            </Button>
          ))}
        </div>
      </div>

      {data.my_position === null && (
        <p style={{ opacity: 0.75, textAlign: 'center' }}>Вас пока нет в рейтинге этой недели</p>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {data.entries.map((entry) => {
            const isMe = entry.client_id === user?.id;
            return (
              <tr
                key={entry.client_id}
                data-me={isMe ? 'true' : 'false'}
                style={{ background: isMe ? 'var(--color-primary-light, rgba(181, 80, 42, 0.12))' : 'transparent', fontWeight: isMe ? 700 : 400 }}
              >
                <td style={{ padding: '10px 8px', width: 48 }}>#{entry.position}</td>
                <td style={{ padding: '10px 8px' }}>{entry.display_name}{isMe ? ' (вы)' : ''}</td>
                <td style={{ padding: '10px 8px', textAlign: 'right' }}>{entry.visits}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
