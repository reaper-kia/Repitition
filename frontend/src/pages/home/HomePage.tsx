import { Link } from 'react-router-dom';
import { useUser } from '../../entities/user/useUser';
import type { Role } from '../../shared/api/types';
import { Button } from '../../shared/ui/Button';

const ROLE_HOME: Record<Role, string> = {
  CLIENT: '/cabinet',
  CLUB_MANAGER: '/manager',
  NETWORK_ADMIN: '/admin',
};

export function HomePage() {
  const { user } = useUser();

  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: '80px 16px' }}>
      <p style={{ letterSpacing: '0.2em', textTransform: 'uppercase', opacity: 0.7 }}>Fit Loyalty</p>
      <h1 style={{ fontSize: '3rem', lineHeight: 1.1, margin: '16px 0' }}>
        Лояльность, которая приводит клиентов снова
      </h1>
      <p style={{ opacity: 0.8, maxWidth: 560, marginBottom: 32 }}>
        Ранги, достижения, скидки и предиктивные карточки риска для управляющих клубом.
      </p>
      <Link to={user ? ROLE_HOME[user.role] : '/login'}>
        <Button>{user ? 'Перейти в кабинет' : 'Войти'}</Button>
      </Link>
    </main>
  );
}
