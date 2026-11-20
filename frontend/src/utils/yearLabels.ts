import { sortedYears } from '@/data/years';

/**
 * Внутренние годы хранятся в астрономической системе: 0 — это 1 г. до н.э.,
 * -1 — 2 г. до н.э. и так далее. Для показа сдвигаем неположительные годы
 * на один назад: 0 → -1, -40 → -41, -500 → -501.
 */
export function toDisplayYear(year: number): number {
  return year <= 0 ? year - 1 : year;
}

export function formatYearTick(year: number): string {
  return String(toDisplayYear(year));
}

export function formatYearHuman(year: number): string {
  const display = toDisplayYear(year);
  return display <= 0 ? `${-display} до н.э.` : String(display);
}

export function getYearQueryRange(year: number): {
  begin: number;
  end: number;
} {
  const index = sortedYears.indexOf(year);
  if (index === -1) return { begin: year, end: year };

  const previousYear = sortedYears[index - 1];
  if (previousYear === undefined) {
    // The earliest map covers all earlier years as well.
    return { begin: Number.MIN_SAFE_INTEGER, end: year };
  }

  return {
    begin: previousYear + 1,
    end: year,
  };
}

export function formatYearPeriod(year: number): string {
  const index = sortedYears.indexOf(year);
  if (index === -1) return formatYearHuman(year);

  const previousYear = sortedYears[index - 1];
  if (previousYear === undefined) return `до ${formatYearHuman(year)}`;

  const startYear = previousYear + 1;
  if (startYear === year) return formatYearHuman(year);

  const displayStart = toDisplayYear(startYear);
  const displayEnd = toDisplayYear(year);

  if (displayStart <= 0 && displayEnd <= 0) {
    return `${-displayStart}-${-displayEnd} до н.э.`;
  }

  if (displayStart > 0 && displayEnd > 0) {
    return `${displayStart}-${displayEnd}`;
  }

  return `${formatYearHuman(startYear)}-${formatYearHuman(year)}`;
}
