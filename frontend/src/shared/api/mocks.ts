import type {
  ApiClient,
  MeResponse,
  RankProgress,
  AchievementItem,
  ChallengeProgress,
  DiscountGrantItem,
  RetentionCaseSummary,
  LoginRequest,
  RegisterRequest,
  ResolveCaseRequest,
} from './types';

const ACCOUNTS_KEY = 'mock_registered_users_v1';
const SESSION_KEY = 'mock_current_session_v1';

interface StoredAccount {
  user: MeResponse;
  password: string;
}

const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));
const randomDelay = () => delay(300 + Math.random() * 300);

const MOCK_CLIENT: MeResponse = { id: '1', name: 'Анна Иванова', email: 'anna@mail.com', role: 'CLIENT' };
const MOCK_MANAGER: MeResponse = { id: '2', name: 'Пётр Сидоров', email: 'manager@mail.com', role: 'CLUB_MANAGER' };
const MOCK_ADMIN: MeResponse = { id: '3', name: 'Иван Петров', email: 'admin@mail.com', role: 'NETWORK_ADMIN' };

const PRESET: Record<string, MeResponse> = {
  'anna@mail.com': MOCK_CLIENT,
  'manager@mail.com': MOCK_MANAGER,
  'admin@mail.com': MOCK_ADMIN,
};

function loadAccounts(): Record<string, StoredAccount> {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, StoredAccount>;
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function saveAccounts(): void {
  try {
    localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
  } catch {
    // localStorage недоступен — молча пропускаем
  }
}

let accounts: Record<string, StoredAccount> = loadAccounts();
let currentUser: MeResponse | null = null;

function setSession(user: MeResponse | null): void {
  currentUser = user;
  try {
    if (user) localStorage.setItem(SESSION_KEY, user.email);
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    // игнорируем
  }
}

function restoreSession(): MeResponse | null {
  try {
    const email = localStorage.getItem(SESSION_KEY);
    if (!email) return null;
    if (PRESET[email]) return PRESET[email];
    const acc = accounts[email];
    return acc ? acc.user : null;
  } catch {
    return null;
  }
}

const annaRank: RankProgress = { code: 'REGULAR', title: 'Завсегдатай', visits_total: 34, next_title: 'Атлет', visits_to_next: 46 };
const managerRank: RankProgress = { code: 'MAX', title: 'Легенда', visits_total: 120, next_title: null, visits_to_next: null };
const newbieRank: RankProgress = { code: 'NEW', title: 'Новичок', visits_total: 0, next_title: 'Завсегдатай', visits_to_next: 10 };

const annaAchievements: AchievementItem[] = [
  { code: 'FIRST', title: 'Первый визит', icon: '🎉', earned: true, achieved_at: '2025-08-15T10:00:00Z' },
  { code: 'STREAK_7', title: '7 дней подряд', icon: '🔥', earned: true, achieved_at: '2025-09-01T10:00:00Z' },
  { code: 'STREAK_30', title: '30 дней подряд', icon: '🏆', earned: false, achieved_at: null },
  { code: 'FRIEND', title: 'Привёл друга', icon: '👥', earned: false, achieved_at: null },
  { code: 'EARLY_BIRD', title: 'Ранняя пташка', icon: '🌅', earned: true, achieved_at: '2025-08-20T06:00:00Z' },
];
const newbieAchievements: AchievementItem[] = annaAchievements.map((a) => ({ ...a, earned: false, achieved_at: null }));

const annaGrants: DiscountGrantItem[] = [
  { grant_id: 'g1', amount: '1500.00', purpose: 'REFERRAL_INVITEE', applicable_purchase_type: 'MEMBERSHIP', valid_until: new Date(Date.now() + 5 * 86400000).toISOString(), status: 'AVAILABLE' },
  { grant_id: 'g2', amount: '13000.00', purpose: 'RETENTION', applicable_purchase_type: 'RENEWAL', valid_until: new Date(Date.now() + 2 * 86400000).toISOString(), status: 'AVAILABLE' },
  { grant_id: 'g3', amount: '500.00', purpose: 'REFERRAL_REFERRER', applicable_purchase_type: 'PERSONAL_TRAINING', valid_until: new Date(Date.now() - 86400000).toISOString(), status: 'EXPIRED' },
  { grant_id: 'g4', amount: '2000.00', purpose: 'RETENTION', applicable_purchase_type: 'PRODUCT', valid_until: new Date(Date.now() + 30 * 86400000).toISOString(), status: 'REDEEMED' },
];
const newbieGrants: DiscountGrantItem[] = [];

const annaChallenge: ChallengeProgress = { current_stage: 2, total_stages: 3, visits_in_stage: 4, required_visits: 6, status: 'IN_PROGRESS' };
const newbieChallenge: ChallengeProgress = { current_stage: 1, total_stages: 3, visits_in_stage: 0, required_visits: 3, status: 'IN_PROGRESS' };

const retentionCases: RetentionCaseSummary[] = [
  { case_id: 'c1', client_id: '10', client_name: 'Иван Петров', risk_score: 0.87, risk_reasons: ['11 дней без визита при обычных 4', 'Пропали групповые занятия'], detected_at: '2025-09-05T10:00:00Z' },
  { case_id: 'c2', client_id: '11', client_name: 'Мария Сидорова', risk_score: 0.72, risk_reasons: ['Сократилось количество визитов', 'Не покупает абонементы'], detected_at: '2025-09-04T10:00:00Z' },
  { case_id: 'c3', client_id: '12', client_name: 'Алексей Смирнов', risk_score: 0.55, risk_reasons: ['Последний визит 2 недели назад'], detected_at: '2025-09-03T10:00:00Z' },
  { case_id: 'c4', client_id: '13', client_name: 'Ольга Кузнецова', risk_score: 0.38, risk_reasons: ['Уменьшилась частота визитов'], detected_at: '2025-09-02T10:00:00Z' },
  { case_id: 'c5', client_id: '14', client_name: 'Дмитрий Попов', risk_score: 0.15, risk_reasons: ['Сезонное снижение активности'], detected_at: '2025-09-01T10:00:00Z' },
];

function isPreset(): boolean {
  return currentUser !== null && Boolean(PRESET[currentUser.email]);
}

export const mockApi: ApiClient = {
  async getMe() {
    await randomDelay();
    if (!currentUser) currentUser = restoreSession();
    if (!currentUser) throw { status: 401, code: 'UNAUTHENTICATED', message: 'Not logged in' };
    return currentUser;
  },

  async login(data: LoginRequest) {
    await randomDelay();
    const email = data.email.trim().toLowerCase();
    if (PRESET[email]) {
      setSession(PRESET[email]);
      return { user: PRESET[email], referral_discount_promised: false };
    }
    const acc = accounts[email];
    if (!acc || acc.password !== data.password) {
      throw { status: 401, code: 'UNAUTHENTICATED', message: 'Неверный email или пароль' };
    }
    setSession(acc.user);
    return { user: acc.user, referral_discount_promised: false };
  },

  async register(data: RegisterRequest) {
    await randomDelay();
    const email = data.email.trim().toLowerCase();
    if (data.referral_code && data.referral_code !== 'ABC123') {
      throw { status: 422, code: 'INVALID_REFERRAL_CODE', message: 'Код не найден', details: { referral_code: ['Код не найден'] } };
    }
    if (PRESET[email] || accounts[email]) {
      throw { status: 409, code: 'CLIENT_ALREADY_EXISTS', message: 'Аккаунт уже существует' };
    }
    const newUser: MeResponse = {
      id: 'u' + String(Object.keys(accounts).length + 10),
      name: data.name.trim(),
      email,
      role: 'CLIENT',
    };
    accounts[email] = { user: newUser, password: data.password };
    saveAccounts();
    setSession(newUser);
    return { user: newUser, referral_discount_promised: Boolean(data.referral_code) };
  },

  async logout() {
    await randomDelay();
    setSession(null);
  },

  async getClubs() {
    await randomDelay();
    return [
      { club_id: 'club1', name: 'Iron Gym' },
      { club_id: 'club2', name: 'FitZone' },
    ];
  },

  async getRank() {
    await randomDelay();
    if (!currentUser) throw { status: 401, code: 'UNAUTHENTICATED', message: 'Not logged in' };
    if (currentUser.role !== 'CLIENT') return managerRank;
    return isPreset() && currentUser.email === 'anna@mail.com' ? annaRank : newbieRank;
  },

  async getAchievements() {
    await randomDelay();
    return currentUser?.email === 'anna@mail.com' ? annaAchievements : newbieAchievements;
  },

  async getChallenge() {
    await randomDelay();
    return currentUser?.email === 'anna@mail.com' ? annaChallenge : newbieChallenge;
  },

  async getGrants() {
    await randomDelay();
    return currentUser?.email === 'anna@mail.com' ? annaGrants : newbieGrants;
  },

  async getRetentionCases() {
    await randomDelay();
    return retentionCases;
  },

  async resolveCase(caseId: string, _data: ResolveCaseRequest) {
    await randomDelay();
    const idx = retentionCases.findIndex((c) => c.case_id === caseId);
    if (idx >= 0) retentionCases.splice(idx, 1);
  },

  async purchase() {
    await randomDelay();
  },

  async getLeaderboard() {
    await randomDelay();
    const isAnna = currentUser?.email === 'anna@mail.com';
    return {
      week: '2025-W36',
      entries: [
        { position: 1, client_id: '1', display_name: 'Анна И.', visits: 12 },
        { position: 2, client_id: '5', display_name: 'Максим С.', visits: 10 },
        { position: 3, client_id: '6', display_name: 'Елена К.', visits: 8 },
        { position: 4, client_id: '7', display_name: 'Олег Р.', visits: 7 },
      ],
      my_position: isAnna ? 1 : null,
      my_visits: isAnna ? 12 : null,
    };
  },
};