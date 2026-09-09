import { apiClient } from '../../shared/api/client';
import type { MeResponse, LoginRequest, RegisterRequest, AuthResponse, ClubSummary } from '../../shared/api/types';

export const authApi = {
  login(data: LoginRequest): Promise<AuthResponse> {
    return apiClient.post('/api/v1/auth/login', data);
  },
  register(data: RegisterRequest): Promise<AuthResponse> {
    return apiClient.post('/api/v1/auth/register', data);
  },
  logout(): Promise<void> {
    return apiClient.post('/api/v1/auth/logout', {});
  },
  me(): Promise<MeResponse> {
    return apiClient.get('/api/v1/users/me');
  },
  getClubs(): Promise<ClubSummary[]> {
    return apiClient.get('/api/v1/clubs');
  },
};