import { describe, expect, it } from 'vitest';
import {
  formatYearHuman,
  formatYearPeriod,
  formatYearTick,
  getYearQueryRange,
  toDisplayYear,
} from '../yearLabels';

describe('yearLabels', () => {
  it('shifts non-positive astronomical years for display', () => {
    expect(toDisplayYear(0)).toBe(-1);
    expect(toDisplayYear(-1)).toBe(-2);
    expect(toDisplayYear(-40)).toBe(-41);
    expect(toDisplayYear(-500)).toBe(-501);
    expect(toDisplayYear(1)).toBe(1);
    expect(toDisplayYear(1900)).toBe(1900);
  });

  it('formats tick labels without special casing year zero', () => {
    expect(formatYearTick(0)).toBe('-1');
    expect(formatYearTick(-10)).toBe('-11');
    expect(formatYearTick(1900)).toBe('1900');
  });

  it('formats human-readable years', () => {
    expect(formatYearHuman(0)).toBe('1 до н.э.');
    expect(formatYearHuman(-500)).toBe('501 до н.э.');
    expect(formatYearHuman(1900)).toBe('1900');
  });

  it('includes year zero in the query range', () => {
    expect(getYearQueryRange(0)).toEqual({ begin: -9, end: 0 });
    expect(getYearQueryRange(10)).toEqual({ begin: 1, end: 10 });
  });

  it('formats period labels with display years', () => {
    expect(formatYearPeriod(0)).toBe('10-1 до н.э.');
    expect(formatYearPeriod(-10)).toBe('20-11 до н.э.');
    expect(formatYearPeriod(10)).toBe('1-10');
    expect(formatYearPeriod(1900)).toBe('1900');
    expect(formatYearPeriod(-3000)).toBe('до 3001 до н.э.');
  });
});
