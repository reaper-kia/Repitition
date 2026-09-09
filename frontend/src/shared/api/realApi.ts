import { apiClient } from './client';
import type { ApiClient } from './types';

export const realApi: ApiClient = {
  getMe: () => apiClient.get('/api/v1/users/me'),
  login: (data) => apiClient.post('/api/v1/auth/login', data),
  register: (data) => apiClient.post('/api/v1/auth/register', data),
  logout: () => apiClient.post('/api/v1/auth/logout', {}),
  getClubs: () => apiClient.get('/api/v1/clubs'),
  getRank: () => apiClient.get('/api/v1/clients/me/rank'),
  getAchievements: () => apiClient.get('/api/v1/clients/me/achievements'),
  getChallenge: () => apiClient.get('/api/v1/clients/me/challenge'),
  getGrants: () => apiClient.get('/api/v1/clients/me/grants'),
  getRetentionCases: (clubId, page) => apiClient.get(`/api/v1/clubs/${clubId}/retention-cases?page=${page}`),
  resolveCase: (caseId, data, key) =>
    apiClient.post(`/api/v1/retention-cases/${caseId}/resolve`, data, {
      headers: { 'Idempotency-Key': key },
    }),
  purchase: (data, key) =>
    apiClient.post('/api/v1/purchases', data, {
      headers: { 'Idempotency-Key': key },
    }),
  getLeaderboard: (clubId, week) => apiClient.get(`/api/v1/clubs/${clubId}/leaderboard?week=${week}`),
};