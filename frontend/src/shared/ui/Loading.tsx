export function Loading({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <span className="loading__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
