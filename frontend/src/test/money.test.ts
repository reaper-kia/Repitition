import { describe, expect, it } from 'vitest';
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
