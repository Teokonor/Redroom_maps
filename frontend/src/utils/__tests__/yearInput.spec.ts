import { describe, expect, it } from 'vitest';
import {
  findMapYear,
  parseYearInput,
  resolveInputYear,
} from '@/utils/yearInput';

describe('parseYearInput', () => {
  it('parses plain years', () => {
    expect(parseYearInput('1623')).toBe(1623);
    expect(parseYearInput(' 2025 ')).toBe(2025);
  });

  it('parses BC years as display years', () => {
    expect(parseYearInput('-501')).toBe(-500);
    expect(parseYearInput('501 до н.э.')).toBe(-500);
    expect(parseYearInput('501 г. до н. э.')).toBe(-500);
  });

  it('rejects invalid input', () => {
    expect(parseYearInput('')).toBeNull();
    expect(parseYearInput('abc')).toBeNull();
    expect(parseYearInput('16.23')).toBeNull();
  });
});

describe('findMapYear', () => {
  it('returns the map that covers the period', () => {
    expect(findMapYear(1623)).toBe(1630);
    expect(findMapYear(2001)).toBe(2010);
    expect(findMapYear(2005)).toBe(2010);
    expect(findMapYear(2011)).toBe(2020);
    expect(findMapYear(2021)).toBe(2025);
  });

  it('keeps existing map years', () => {
    expect(findMapYear(1993)).toBe(1993);
    expect(findMapYear(2025)).toBe(2025);
  });

  it('uses the earliest map for older years', () => {
    expect(findMapYear(-3999)).toBe(-3000);
    expect(findMapYear(-1054)).toBe(-1000);
  });

  it('has no map for years after the last one', () => {
    expect(findMapYear(2026)).toBeNull();
  });
});

describe('resolveInputYear', () => {
  it('resolves user input to a map year', () => {
    expect(resolveInputYear('1623')).toBe(1630);
    expect(resolveInputYear('-1055')).toBe(-1000);
    expect(resolveInputYear('501 до н.э.')).toBe(-500);
    expect(resolveInputYear('2026')).toBeNull();
    expect(resolveInputYear('abc')).toBeNull();
  });
});
