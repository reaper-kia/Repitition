import { useState } from 'react';
import type { RetentionCaseSummary } from '../../shared/api/types';
import { Button } from '../../shared/ui/Button';

interface Props {
  data: RetentionCaseSummary;
  onResolve: (caseId: string, decision: 'OFFER_DISCOUNT' | 'REJECT') => Promise<void>;
}

function riskColor(score: number): string {
  if (score >= 0.7) return 'var(--color-error, #c0392b)';
  if (score >= 0.4) return 'var(--color-warning, #b7791f)';
  return 'var(--color-text-secondary, #777)';
}

export function RetentionCaseCard({ data, onResolve }: Props) {
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = async (decision: 'OFFER_DISCOUNT' | 'REJECT') => {
    if (processing) return;
    setProcessing(true);
    setError(null);
    try {
      await onResolve(data.case_id, decision);
    } catch (e) {
      const code = (e as { code?: string }).code;
      setError(code === 'INSUFFICIENT_FUNDS' ? 'Фонд клуба на этот месяц исчерпан' : 'Не удалось обработать карточку');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>{data.client_name}</h3>
        <span style={{ fontWeight: 700, color: riskColor(data.risk_score) }}>
          риск {data.risk_score.toFixed(2)}
        </span>
      </div>
      <ul style={{ margin: '0 0 16px', paddingLeft: 20, opacity: 0.85 }}>
        {data.risk_reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div style={{ display: 'flex', gap: 8 }}>
        <Button loading={processing} disabled={processing} onClick={() => void handle('OFFER_DISCOUNT')}>
          Предложить скидку
        </Button>
        <Button variant="secondary" loading={processing} disabled={processing} onClick={() => void handle('REJECT')}>
          Отклонить
        </Button>
      </div>
    </div>
  );
}
