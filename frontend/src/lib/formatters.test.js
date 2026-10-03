import { describe, expect, it } from 'vitest';
import { formatCalories, formatNumber, progressPercent } from './formatters.js';

describe('formatters', () => {
  it('formats calories and numbers for a compact dashboard', () => {
    expect(formatNumber(1840)).toBe('1,840');
    expect(formatCalories(1840)).toBe('1,840 kcal');
  });

  it('clamps progress between zero and one hundred', () => {
    expect(progressPercent(500, 2000)).toBe(25);
    expect(progressPercent(2500, 2000)).toBe(100);
    expect(progressPercent(-20, 2000)).toBe(0);
  });
});
