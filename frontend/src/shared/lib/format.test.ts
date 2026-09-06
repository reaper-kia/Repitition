import { describe, expect, it } from 'vitest';
import { combineLocalDateTime, formatMoney } from './format';

describe('formatMoney', () => {
  it('formats backend decimal strings with the requested currency', () => {
    expect(formatMoney('12.50', 'EUR', 'en-GB')).toContain('12.50');
    expect(formatMoney('12.50', 'EUR', 'en-GB')).toMatch(/€|EUR/);
  });

  it('returns a safe fallback for invalid amounts', () => {
    expect(formatMoney('invalid', 'USD')).toBe('— USD');
  });
});

describe('combineLocalDateTime', () => {
  it('returns a valid ISO timestamp', () => {
    expect(combineLocalDateTime('2030-01-02', '10:30')).toMatch(/^2030-01-02T/);
  });
});
