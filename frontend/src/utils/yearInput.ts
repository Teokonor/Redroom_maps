import { sortedYears } from '@/data/years';

/**
 * Разбирает ввод пользователя в внутренний астрономический год.
 * Поддерживаются числа и запись вида «501 до н.э.».
 */
export function parseYearInput(raw: string): number | null {
  const value = raw.trim();
  if (!value) return null;

  const bcMatch = value.match(
    /^(\d+)\s*(?:г\.?)?\s*(?:до\s*н\.?\s*э\.?|до\s+нашей\s+эры|bc|bce)$/i
  );

  if (bcMatch) {
    const displayYear = Number(bcMatch[1]);
    return displayYear > 0 ? -(displayYear - 1) : null;
  }

  if (!/^[+-]?\d+$/.test(value)) return null;

  const displayYear = Number(value);
  if (!Number.isInteger(displayYear)) return null;

  // В шкале отрицательные годы показаны как -1, -2 и т.д.
  // Внутренний астрономический год сдвинут на единицу: -1 → 0.
  return displayYear < 0 ? displayYear + 1 : displayYear;
}

/**
 * Находит карту, которая покрывает внутренний год.
 * Карта N описывает период от предыдущей карты + 1 до N.
 */
export function findMapYear(target: number): number | null {
  const first = sortedYears[0];
  const last = sortedYears[sortedYears.length - 1];

  if (first === undefined || last === undefined) return null;
  if (target <= first) return first;
  // Более поздних карт, чем последняя, нет.
  if (target > last) return null;

  let low = 0;
  let high = sortedYears.length - 1;
  let result = last;

  while (low <= high) {
    const middle = (low + high) >> 1;
    const year = sortedYears[middle];

    if (year === undefined) break;

    if (year >= target) {
      result = year;
      high = middle - 1;
    } else {
      low = middle + 1;
    }
  }

  return result;
}

export function resolveInputYear(raw: string): number | null {
  const target = parseYearInput(raw);
  return target === null ? null : findMapYear(target);
}
