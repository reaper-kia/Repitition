import { api } from '../../shared/api';
import { formatMoney } from '../../shared/lib/formatMoney';
import { useAsync } from '../../shared/lib/useAsync';
import { EmptyState } from '../../shared/ui/EmptyState';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

const PURPOSE_LABELS: Record<string, string> = {
  REFERRAL_INVITEE: 'За регистрацию по приглашению',
  REFERRAL_REFERRER: 'За приглашение друга',
  RETENTION: 'Специальное предложение',
};

const PURPOSE_PURCHASE: Record<string, string> = {
  MEMBERSHIP: 'абонемент',
  RENEWAL: 'продление',
  PERSONAL_TRAINING: 'персональные тренировки',
  PRODUCT: 'товары',
};

export function GrantsList() {
  const { data, loading, error, reload } = useAsync(() => api.getGrants(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;

  const available = (data ?? []).filter((g) => g.status === 'AVAILABLE');
  if (available.length === 0) {
    return <EmptyState title="Пока нет доступных скидок" message="Пригласите друга — и скидка появится здесь." />;
  }

  const now = Date.now();
  const sevenDays = 7 * 24 * 60 * 60 * 1000;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {available.map((g) => {
        const expiresSoon = new Date(g.valid_until).getTime() - now < sevenDays;
        return (
          <div key={g.grant_id} className="card" style={{ padding: 16, display: 'flex', justifyContent: 'space-between', gap: 12 }}>
            <div>
              <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>{formatMoney(g.amount)}</div>
              <div style={{ opacity: 0.75, fontSize: '0.875rem' }}>
                {PURPOSE_LABELS[g.purpose] ?? g.purpose} · {PURPOSE_PURCHASE[g.applicable_purchase_type] ?? g.applicable_purchase_type}
              </div>
            </div>
            <div style={{ textAlign: 'right', fontSize: '0.875rem' }}>
              <div>до {new Date(g.valid_until).toLocaleDateString('ru-RU')}</div>
              {expiresSoon && <div style={{ color: 'var(--color-warning, #b7791f)', fontWeight: 600 }}>истекает скоро</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
