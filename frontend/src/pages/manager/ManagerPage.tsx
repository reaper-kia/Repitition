import { useCallback, useState } from 'react';
import { useToast } from '../../app/providers/ToastProvider';
import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { Button } from '../../shared/ui/Button';
import { EmptyState } from '../../shared/ui/EmptyState';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';
import { RetentionCaseCard } from '../../widgets/retention/RetentionCaseCard';

const CLUB_ID = 'club1';

export function ManagerPage() {
  const { showToast } = useToast();
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useAsync(
    () => api.getRetentionCases(CLUB_ID, page),
    [page],
  );

  const handleResolve = useCallback(
    async (caseId: string, decision: 'OFFER_DISCOUNT' | 'REJECT') => {
      await api.resolveCase(
        caseId,
        { decision, amount: decision === 'OFFER_DISCOUNT' ? '1500.00' : undefined },
        crypto.randomUUID(),
      );
      showToast(decision === 'OFFER_DISCOUNT' ? 'Скидка предложена клиенту' : 'Карточка отклонена', 'success');
      await reload();
    },
    [reload, showToast],
  );

  if (loading) return <div className="route-state"><Loading /></div>;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;

  return (
    <main style={{ maxWidth: 860, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ marginBottom: 24 }}>Карточки риска</h1>
      {!data || data.length === 0 ? (
        <EmptyState title="Все клиенты ходят стабильно" message="Новые карточки появятся здесь автоматически." />
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>
            {data.map((c) => (
              <RetentionCaseCard key={c.case_id} data={c} onResolve={handleResolve} />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, alignItems: 'center' }}>
            <Button variant="secondary" disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Назад
            </Button>
            <span>Страница {page}</span>
            <Button variant="secondary" disabled={data.length < 20} onClick={() => setPage((p) => p + 1)}>
              Вперёд
            </Button>
          </div>
        </>
      )}
    </main>
  );
}
