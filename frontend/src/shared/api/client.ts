const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

const statusMessages: Record<number, string> = {
  400: 'Некорректные данные запроса',
  401: 'Требуется войти в систему',
  403: 'Недостаточно прав',
  404: 'Данные не найдены',
  409: 'Конфликт данных',
  422: 'Проверьте заполненные поля',
  429: 'Слишком много запросов. Попробуйте позже',
  500: 'Сервис временно недоступен',
};

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function extractError(payload: unknown, status: number): { message: string; code?: string; details?: unknown } {
  if (payload && typeof payload === 'object') {
    const detail = 'detail' in payload ? payload.detail : undefined;
    const message = 'message' in payload ? payload.message : undefined;
    const code = 'code' in payload ? payload.code : undefined;
    const details = 'details' in payload ? payload.details : undefined;
    
    if (typeof detail === 'string') return { message: detail, code: code as string | undefined, details };
    if (typeof message === 'string') return { message, code: code as string | undefined, details };
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (first && typeof first === 'object' && 'msg' in first && typeof first.msg === 'string') {
        return { message: first.msg.replace(/^Value error,\s*/i, ''), code: code as string | undefined, details };
      }
    }
    if (details) return { message: statusMessages[status] ?? `Ошибка запроса (${status})`, code: code as string | undefined, details };
  }
  return { message: statusMessages[status] ?? `Ошибка запроса (${status})` };
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const hasBody = options.body !== undefined;
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => undefined);
    const errorInfo = extractError(payload, response.status);
    throw new ApiError(errorInfo.message, response.status, errorInfo.code, errorInfo.details);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(endpoint: string, options?: { signal?: AbortSignal; headers?: Record<string, string> }) =>
    request<T>(endpoint, { method: 'GET', signal: options?.signal, headers: options?.headers }),
  post: <T>(endpoint: string, body: unknown, options?: { headers?: Record<string, string> }) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(body), headers: options?.headers }),
  patch: <T>(endpoint: string, body?: unknown, options?: { headers?: Record<string, string> }) =>
    request<T>(endpoint, {
      method: 'PATCH',
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      headers: options?.headers,
    }),
  delete: <T>(endpoint: string, options?: { headers?: Record<string, string> }) =>
    request<T>(endpoint, { method: 'DELETE', headers: options?.headers }),
};