import { years } from '@/data/years';

const sortedYears = [...years].sort((a, b) => a - b);
const PERIOD_ARROW = '→';

export function formatYearTick(year: number): string {
  return year === 0 ? `-1${PERIOD_ARROW}1` : String(year);
}

export function getYearQueryRange(year: number): {
  begin: number;
  end: number;
} {
  const index = sortedYears.indexOf(year);
  if (index === -1) return { begin: year, end: year };

  if (year === 0) {
    const previousYear = sortedYears[index - 1];
    return {
      begin: previousYear === undefined ? year : previousYear + 1,
      end: -1,
    };
  }

  const previousYear = sortedYears[index - 1];
  if (previousYear === undefined) {
    // The earliest map covers all earlier years as well.
    return { begin: Number.MIN_SAFE_INTEGER, end: year };
  }

  return { begin: previousYear + 1, end: year };
}

export function formatYearPeriod(year: number): string {
  const index = sortedYears.indexOf(year);
  if (index === -1) return String(year);

  if (year === 0) {
    const previousYear = sortedYears[index - 1];
    if (previousYear === undefined) return String(year);
    return `${previousYear + 1}${PERIOD_ARROW}-1`;
  }

  const previousYear = sortedYears[index - 1];
  if (previousYear === undefined) return `до ${year}`;

  const startYear = previousYear + 1;
  return startYear === year ? String(year) : `${startYear}${PERIOD_ARROW}${year}`;
}
