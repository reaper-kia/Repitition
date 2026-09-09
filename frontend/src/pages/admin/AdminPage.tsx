import { useUser } from '../../entities/user/useUser';
import { StatsCharts } from '../../widgets/charts/StatsCharts';
import { Leaderboard } from '../../widgets/leaderboard/Leaderboard';

export function AdminPage() {
  const { user } = useUser();

  return (
    <main style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ marginBottom: 24 }}>Панель сети · {user?.name}</h1>
      <section style={{ marginBottom: 32 }}><Leaderboard /></section>
      <section>
        <h2 style={{ marginBottom: 16 }}>Статистика</h2>
        <StatsCharts />
      </section>
    </main>
  );
}
