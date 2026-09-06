import { describe, expect, it, vi } from 'vitest';
import { isFutureDateTime, isValidContact } from './validation';

describe('request validation', () => {
  it('accepts email or phone-like contacts', () => {
    expect(isValidContact('test@example.com')).toBe(true);
    expect(isValidContact('+7 900 123 45 67')).toBe(true);
    expect(isValidContact('abc')).toBe(false);
  });

  it('accepts only future local date times', () => {
    vi.setSystemTime(new Date('2029-01-01T12:00:00Z'));
    expect(isFutureDateTime('2030-01-01', '12:00')).toBe(true);
    expect(isFutureDateTime('2028-01-01', '12:00')).toBe(false);
    vi.useRealTimers();
  });
});
