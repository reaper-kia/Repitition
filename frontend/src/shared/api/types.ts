export type Role = 'CLIENT' | 'CLUB_MANAGER' | 'NETWORK_ADMIN';

export interface MeResponse {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface RankProgress {
  code: string;
  title: string;
  visits_total: number;
  next_title: string | null;
  visits_to_next: number | null;
}

export interface AchievementItem {
  code: string;
  title: string;
  icon: string;
  earned: boolean;
  achieved_at: string | null;
}

export interface ChallengeProgress {
  current_stage: number;
  total_stages: number;
  visits_in_stage: number;
  required_visits: number;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'EXPIRED';
}

export interface LeaderboardEntry {
  position: number;
  client_id: string;
  display_name: string;
  visits: number;
}

export interface LeaderboardResponse {
  week: string;
  entries: LeaderboardEntry[];
  my_position: number | null;
  my_visits: number | null;
}

export interface DiscountGrantItem {
  grant_id: string;
  amount: string;
  purpose: 'REFERRAL_INVITEE' | 'REFERRAL_REFERRER' | 'RETENTION';
  applicable_purchase_type: 'MEMBERSHIP' | 'RENEWAL' | 'PERSONAL_TRAINING' | 'PRODUCT';
  valid_until: string;
  status: 'AVAILABLE' | 'REDEEMED' | 'EXPIRED' | 'CANCELLED';
}

export interface RetentionCaseSummary {
  case_id: string;
  client_id: string;
  client_name: string;
  risk_score: number;
  risk_reasons: string[];
  detected_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  club_id: string;
  subscription_type: string;
  referral_code?: string;
}

export interface AuthResponse {
  user: MeResponse;
  referral_discount_promised?: boolean;
}

export interface ClubSummary {
  club_id: string;
  name: string;
}

export interface PurchaseRequest {
  client_id: string;
  purchase_type: 'MEMBERSHIP' | 'RENEWAL' | 'PERSONAL_TRAINING' | 'PRODUCT';
  amount: string;
  grant_ids: string[];
}

export interface ResolveCaseRequest {
  decision: 'OFFER_DISCOUNT' | 'REJECT';
  amount?: string;
  comment?: string;
}

export interface ApiClient {
  getMe(): Promise<MeResponse>;
  login(data: LoginRequest): Promise<AuthResponse>;
  register(data: RegisterRequest): Promise<AuthResponse>;
  logout(): Promise<void>;
  getClubs(): Promise<ClubSummary[]>;
  getRank(): Promise<RankProgress>;
  getAchievements(): Promise<AchievementItem[]>;
  getChallenge(): Promise<ChallengeProgress>;
  getGrants(): Promise<DiscountGrantItem[]>;
  getRetentionCases(clubId: string, page: number): Promise<RetentionCaseSummary[]>;
  resolveCase(caseId: string, data: ResolveCaseRequest, idempotencyKey: string): Promise<void>;
  purchase(data: PurchaseRequest, idempotencyKey: string): Promise<void>;
  getLeaderboard(clubId: string, week: string): Promise<LeaderboardResponse>;
}