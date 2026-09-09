import { useState, type FormEvent } from 'react';
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
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) e.email = 'Некорректный email';
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
