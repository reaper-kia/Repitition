import { useUser } from '../../entities/user/useUser';
import { AchievementsGrid } from '../../widgets/achievements/AchievementsGrid';
import { ChallengeCard } from '../../widgets/challenge/ChallengeCard';
import { GrantsList } from '../../widgets/grants/GrantsList';
import { RankCard } from '../../widgets/rank/RankCard';

export function CabinetPage() {
  const { user } = useUser();

  return (
    <main style={{ maxWidth: 860, margin: '0 auto', padding: '32px 16px' }}>
      <h1 style={{ marginBottom: 24 }}>Привет, {user?.name}!</h1>
      <section style={{ marginBottom: 32 }}><RankCard /></section>
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ marginBottom: 16 }}>Достижения</h2>
        <AchievementsGrid />
      </section>
      <section style={{ marginBottom: 32 }}><ChallengeCard /></section>
      <section>
        <h2 style={{ marginBottom: 16 }}>Мои скидки</h2>
        <GrantsList />
      </section>
    </main>
  );
}
