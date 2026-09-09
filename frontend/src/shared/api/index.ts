import { mockApi } from './mocks';
import { realApi } from './realApi';
import type { ApiClient } from './types';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export const api: ApiClient = USE_MOCKS ? mockApi : realApi;
export type { ApiClient } from './types';
export * from './types';