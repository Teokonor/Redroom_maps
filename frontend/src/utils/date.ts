const ISO_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})/;

export function formatPublishedDate(
  value: string | null | undefined
): string | null {
  const raw = value?.trim();
  if (!raw) return null;

  const match = ISO_DATE_PATTERN.exec(raw);
  if (!match) return raw;

  const [, year, month, day] = match;
  return `${day}.${month}.${year}`;
}
