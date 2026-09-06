/**
 * Универсальный бейдж статуса.
 *
 * Раньше был жёстко завязан на статусы заявок кофейни. Теперь принимает
 * произвольную строку и опциональный словарь подписей — подставь свои
 * статусы под кейс, CSS-классы status-badge--<status> уже есть в global.css.
 */

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger';

interface StatusBadgeProps {
  status: string;
  label?: string;
  tone?: BadgeTone;
}

export function StatusBadge({ status, label, tone = 'neutral' }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status.toLowerCase()} status-badge--${tone}`}>
      {label ?? status}
    </span>
  );
}
