import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));

const files = {};

files['src/entities/user/useUser.tsx'] = `import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api } from '../../shared/api';
import type { MeResponse } from '../../shared/api/types';

interface UserState {
  user: MeResponse | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

const UserContext = createContext<UserState | null>(null);

export function useUser(): UserState {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used inside UserProvider');
  return ctx;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const me = await api.getMe();
      setUser(me);
      setError(null);
    } catch (e) {
      setUser(null);
      const status = (e as { status?: number }).status;
      setError(status === 401 || status === 403 ? null : 'Не удалось проверить сессию');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <UserContext.Provider value={{ user, loading, error, reload }}>
      {children}
    </UserContext.Provider>
  );
}
`;

files['src/shared/lib/formatMoney.ts'] = `export function formatMoney(amountStr: string): string {
  if (!amountStr) return '0,00 ₽';
  const parts = amountStr.split('.');
  const whole = parts[0];
  const frac = (parts[1] ?? '00').padEnd(2, '0').slice(0, 2);
  const withSpaces = whole.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ');
  return withSpaces + ',' + frac + ' ₽';
}
`;

files['src/shared/lib/useAsync.ts'] = `import { useCallback, useEffect, useRef, useState } from 'react';

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fnRef.current();
      setData(result);
    } catch (e) {
      setError((e as Error)?.message ?? 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, reload };
}
`;

files['src/features/auth/ProtectedRoute.tsx'] = `import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useUser } from '../../entities/user/useUser';
import type { Role } from '../../shared/api/types';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

interface ProtectedRouteProps {
  children: ReactNode;
  allow?: Role[];
}

export function ProtectedRoute({ children, allow }: ProtectedRouteProps) {
  const { user, loading, error, reload } = useUser();
  const location = useLocation();

  if (loading) return <div className="route-state"><Loading /></div>;
  if (error) return <div className="route-state"><ErrorMessage message={error} onRetry={() => void reload()} /></div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (allow && !allow.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
`;

files['src/app/router.tsx'] = `import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../features/auth/ProtectedRoute';
import { AdminPage } from '../pages/admin/AdminPage';
import { CabinetPage } from '../pages/cabinet/CabinetPage';
import { HomePage } from '../pages/home/HomePage';
import { LoginPage } from '../pages/login/LoginPage';
import { ManagerPage } from '../pages/manager/ManagerPage';
import { NotFoundPage } from '../pages/not-found/NotFoundPage';
import { PublicLayout } from '../widgets/layout/PublicLayout';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/cabinet"
            element={<ProtectedRoute allow={['CLIENT']}><CabinetPage /></ProtectedRoute>}
          />
          <Route
            path="/manager"
            element={<ProtectedRoute allow={['CLUB_MANAGER']}><ManagerPage /></ProtectedRoute>}
          />
          <Route
            path="/manager/cases"
            element={<ProtectedRoute allow={['CLUB_MANAGER']}><ManagerPage /></ProtectedRoute>}
          />
          <Route
            path="/admin"
            element={<ProtectedRoute allow={['NETWORK_ADMIN']}><AdminPage /></ProtectedRoute>}
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}
`;

files['src/app/App.tsx'] = `import { UserProvider } from '../entities/user/useUser';
import { ErrorBoundary } from '../shared/ui/ErrorBoundary';
import { AppProviders } from './providers/AppProviders';
import { AppRouter } from './router';

export function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <UserProvider>
          <AppRouter />
        </UserProvider>
      </AppProviders>
    </ErrorBoundary>
  );
}
`;

files['src/pages/login/LoginPage.tsx'] = `import { useState, type FormEvent } from 'react';
import { LockKeyhole } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '../../app/providers/ToastProvider';
import { useUser } from '../../entities/user/useUser';
import { api } from '../../shared/api';
import type { ClubSummary, Role } from '../../shared/api/types';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { Select } from '../../shared/ui/Select';

const ROLE_HOME: Record<Role, string> = {
  CLIENT: '/cabinet',
  CLUB_MANAGER: '/manager',
  NETWORK_ADMIN: '/admin',
};

const SUBSCRIPTION_OPTIONS = [
  { value: '', label: '— выберите тип —' },
  { value: 'MONTHLY', label: 'Месячный' },
  { value: 'YEARLY', label: 'Годовой' },
  { value: 'VISIT', label: 'Разовый' },
];

interface Payload {
  mode: 'login' | 'register';
  name: string;
  email: string;
  password: string;
  clubId: string;
  subscriptionType: string;
  referralCode: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const { reload } = useUser();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [clubs, setClubs] = useState<ClubSummary[]>([]);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [clubId, setClubId] = useState('');
  const [subscriptionType, setSubscriptionType] = useState('');
  const [referralCode, setReferralCode] = useState('');

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [retryPayload, setRetryPayload] = useState<Payload | null>(null);

  const loadClubs = async () => {
    if (clubs.length > 0) return;
    try {
      setClubs(await api.getClubs());
    } catch {
      showToast('Не удалось загрузить список клубов', 'error');
    }
  };

  const switchMode = (next: 'login' | 'register') => {
    setMode(next);
    setErrors({});
    setGeneralError(null);
    if (next === 'register') void loadClubs();
  };

  const validate = (p: Payload): Record<string, string> => {
    const e: Record<string, string> = {};
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(p.email)) e.email = 'Некорректный email';
    if (p.password.length < 8) e.password = 'Пароль не короче 8 символов';
    if (p.mode === 'register') {
      if (!p.name.trim()) e.name = 'Введите имя';
      if (!p.clubId) e.club = 'Выберите клуб';
      if (!p.subscriptionType) e.subscription = 'Выберите тип абонемента';
      if (p.referralCode && !/^[A-Z0-9]{6}$/.test(p.referralCode)) e.referral = '6 символов A-Z0-9';
    }
    return e;
  };

  const submitPayload = async (p: Payload) => {
    setLoading(true);
    setGeneralError(null);
    setRetryPayload(null);
    try {
      const res = p.mode === 'login'
        ? await api.login({ email: p.email, password: p.password })
        : await api.register({
            name: p.name,
            email: p.email,
            password: p.password,
            club_id: p.clubId,
            subscription_type: p.subscriptionType,
            referral_code: p.referralCode || undefined,
          });

      await reload();

      if (p.mode === 'register' && p.referralCode) {
        if (res.referral_discount_promised) {
          showToast('Скидка на первый абонемент начислена', 'success');
        } else {
          showToast('Код принят', 'success');
        }
      }

      const from = (location.state as { from?: string } | null)?.from;
      navigate(from ?? ROLE_HOME[res.user.role], { replace: true });
    } catch (err) {
      const e = err as { status?: number; code?: string; details?: unknown };
      if (e.status === 401) {
        setGeneralError('Неверный email или пароль');
        setPassword('');
      } else if (e.status === 409) {
        setGeneralError('Аккаунт уже существует');
      } else if (e.status === 422 && e.code === 'INVALID_REFERRAL_CODE') {
        setErrors({ referral: 'Код не найден' });
      } else if (e.status === 422 && e.code === 'CLUB_INACTIVE') {
        setErrors({ club: 'Клуб временно недоступен' });
      } else if (e.status === 422 && e.details && typeof e.details === 'object') {
        const mapped: Record<string, string> = {};
        for (const [key, value] of Object.entries(e.details as Record<string, unknown>)) {
          if (Array.isArray(value) && value.length > 0) mapped[key] = String(value[0]);
        }
        setErrors(mapped);
      } else {
        setGeneralError('Сервис недоступен. Попробуйте ещё раз.');
        setRetryPayload(p);
      }
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (loading) return;
    const p: Payload = {
      mode,
      name: name.trim(),
      email: email.trim(),
      password,
      clubId,
      subscriptionType,
      referralCode: referralCode.trim().toUpperCase(),
    };
    const e = validate(p);
    setErrors(e);
    if (Object.keys(e).length > 0) return;
    void submitPayload(p);
  };

  const clubOptions = [
    { value: '', label: '— выберите клуб —' },
    ...clubs.map((c) => ({ value: c.club_id, label: c.name })),
  ];

  return (
    <main className="login-page">
      <div className="login-page__form">
        <form onSubmit={onSubmit} noValidate>
          <span className="login-icon"><LockKeyhole /></span>
          <h1>{mode === 'login' ? 'Вход' : 'Регистрация'}</h1>

          {mode === 'register' && (
            <Input
              label="Имя"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              autoComplete="name"
              required
            />
          )}

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            autoComplete="email"
            required
          />

          <Input
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            minLength={8}
            required
          />

          {mode === 'register' && (
            <>
              <Select
                label="Клуб"
                value={clubId}
                onChange={(e) => setClubId(e.target.value)}
                options={clubOptions}
              />
              {errors.club && <p className="form-error" role="alert">{errors.club}</p>}

              <Select
                label="Тип абонемента"
                value={subscriptionType}
                onChange={(e) => setSubscriptionType(e.target.value)}
                options={SUBSCRIPTION_OPTIONS}
              />
              {errors.subscription && <p className="form-error" role="alert">{errors.subscription}</p>}

              <Input
                label="Реферальный код (необязательно)"
                value={referralCode}
                onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
                error={errors.referral}
                maxLength={6}
                placeholder="ABC123"
              />
            </>
          )}

          {generalError && <p className="form-error" role="alert">{generalError}</p>}
          {retryPayload && (
            <Button type="button" variant="secondary" onClick={() => void submitPayload(retryPayload)}>
              Повторить
            </Button>
          )}

          <Button type="submit" loading={loading}>
            {mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
          </Button>

          <button
            className="login-mode-toggle"
            type="button"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
          </button>
        </form>
      </div>
    </main>
  );
}
`;

files['src/pages/home/HomePage.tsx'] = `import { Link } from 'react-router-dom';
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
`;

files['src/pages/cabinet/CabinetPage.tsx'] = `import { useUser } from '../../entities/user/useUser';
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
`;

files['src/pages/manager/ManagerPage.tsx'] = `import { useCallback, useState } from 'react';
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
`;

files['src/pages/admin/AdminPage.tsx'] = `import { useUser } from '../../entities/user/useUser';
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
`;

files['src/widgets/rank/RankCard.tsx'] = `import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

export function RankCard() {
  const { data, loading, error, reload } = useAsync(() => api.getRank(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data) return null;

  const isMax = data.visits_to_next === null;
  const percent = isMax ? 100 : Math.round((data.visits_total / (data.visits_total + (data.visits_to_next ?? 0))) * 100);

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>{data.title}</h2>
        <span style={{ fontSize: '1.4rem', fontWeight: 600 }}>{data.visits_total} визитов</span>
      </div>
      {isMax ? (
        <p style={{ margin: 0, fontWeight: 600 }}>🏆 Максимальный уровень</p>
      ) : (
        <>
          <p style={{ opacity: 0.75, marginBottom: 12 }}>
            до «{data.next_title}» ещё {data.visits_to_next}
          </p>
          <div style={{ height: 12, borderRadius: 6, background: 'var(--color-border, #ddd)', overflow: 'hidden' }}>
            <div style={{ width: percent + '%', height: '100%', background: 'var(--color-primary, #b5502a)' }} />
          </div>
        </>
      )}
    </div>
  );
}
`;

files['src/widgets/achievements/AchievementsGrid.tsx'] = `import { api } from '../../shared/api';
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
`;

files['src/widgets/challenge/ChallengeCard.tsx'] = `import { api } from '../../shared/api';
import { useAsync } from '../../shared/lib/useAsync';
import { ErrorMessage } from '../../shared/ui/ErrorMessage';
import { Loading } from '../../shared/ui/Loading';

export function ChallengeCard() {
  const { data, loading, error, reload } = useAsync(() => api.getChallenge(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={() => void reload()} />;
  if (!data) return null;

  if (data.status !== 'IN_PROGRESS') {
    return (
      <div className="card" style={{ padding: 24, textAlign: 'center' }}>
        <strong>Программа завершена</strong>
      </div>
    );
  }

  const percent = Math.round((data.visits_in_stage / data.required_visits) * 100);

  return (
    <div className="card" style={{ padding: 24 }}>
      <h3 style={{ marginTop: 0, marginBottom: 8 }}>Онбординг</h3>
      <p style={{ opacity: 0.75, marginBottom: 12 }}>
        Этап {data.current_stage} из {data.total_stages} · {data.visits_in_stage} из {data.required_visits} визитов
      </p>
      <div style={{ height: 12, borderRadius: 6, background: 'var(--color-border, #ddd)', overflow: 'hidden' }}>
        <div style={{ width: percent + '%', height: '100%', background: 'var(--color-primary, #b5502a)' }} />
      </div>
    </div>
  );
}
`;

files['src/widgets/grants/GrantsList.tsx'] = `import { api } from '../../shared/api';
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
`;

files['src/widgets/retention/RetentionCaseCard.tsx'] = `import { useState } from 'react';
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
`;

files['src/widgets/leaderboard/Leaderboard.tsx'] = `import { useState } from 'react';
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
`;

files['src/widgets/charts/StatsCharts.tsx'] = `import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const visits = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  visits: 20 + ((i * 7) % 35),
}));

const fund = [
  { name: 'Лимит', value: 100000 },
  { name: 'Зарезервировано', value: 25000 },
  { name: 'Потрачено', value: 45000 },
];

const funnel = [
  { stage: 'Знакомство', clients: 120 },
  { stage: 'Первый визит', clients: 80 },
  { stage: 'Регулярные', clients: 45 },
  { stage: 'Постоянные', clients: 20 },
];

export function StatsCharts() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Визиты по дням (30 дней)</h3>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={visits}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line type="monotone" dataKey="visits" stroke="#b5502a" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Фонд клуба</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={fund}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#b5502a" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginTop: 0 }}>Воронка онбординга</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={funnel} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="stage" width={110} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="clients" fill="#7a9b76" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
`;

files['src/test/money.test.ts'] = `import { describe, expect, it } from 'vitest';
import { ApiError } from '../shared/api/client';
import { formatMoney } from '../shared/lib/formatMoney';

describe('formatMoney', () => {
  it('форматирует строку без потери копеек', () => {
    expect(formatMoney('13000.00')).toBe('13 000,00 ₽');
  });

  it('дополняет отсутствующие копейки', () => {
    expect(formatMoney('500')).toBe('500,00 ₽');
  });
});

describe('ApiError', () => {
  it('отличает 401 от 422 по status', () => {
    const unauthorized = new ApiError('nope', 401, 'UNAUTHENTICATED');
    const validation = new ApiError('bad', 422, 'VALIDATION_ERROR');
    expect(unauthorized.status).toBe(401);
    expect(validation.status).toBe(422);
    expect(unauthorized.code).toBe('UNAUTHENTICATED');
  });
});
`;

for (const [rel, content] of Object.entries(files)) {
  const full = path.join(root, rel);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, 'utf8');
  console.log('OK  ' + rel);
}

const envPath = path.join(root, '.env');
if (!fs.existsSync(envPath)) {
  fs.writeFileSync(envPath, 'VITE_USE_MOCKS=true\n', 'utf8');
  console.log('OK  .env (создан с VITE_USE_MOCKS=true)');
} else {
  console.log('--  .env уже существует, не трогаю');
}

console.log('\nГотово! Дальше:');
console.log('  npm run typecheck');
console.log('  npm run test');
console.log('  npm run build');
console.log('  npm run dev   (перезапусти, если был запущен)');