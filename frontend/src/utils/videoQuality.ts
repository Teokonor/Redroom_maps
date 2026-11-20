export type VideoQuality = {
  color: string;
  label: string;
};

export function getVideoQuality(
  rawQuality: string | null | undefined
): VideoQuality {
  const raw = rawQuality?.trim() ?? '';
  const normalized = raw.startsWith('#') ? raw.slice(1) : raw;

  if (!/^[0-9a-f]{6}$/i.test(normalized)) {
    return {
      color: '#808080',
      label: 'Качество видео: неизвестно',
    };
  }

  const MAX_CHANNEL = 153;
  const red = parseInt(normalized.slice(0, 2), 16);
  const green = parseInt(normalized.slice(2, 4), 16);
  const redValue = Math.min(MAX_CHANNEL, Math.max(0, red));
  const greenValue = Math.min(MAX_CHANNEL, Math.max(0, green));

  // Градиент двухфазный: красный -> жёлтый (растёт зелёный),
  // затем жёлтый -> зелёный (убывает красный).
  const score =
    greenValue < MAX_CHANNEL
      ? (greenValue / MAX_CHANNEL) * 0.5
      : 0.5 + ((MAX_CHANNEL - redValue) / MAX_CHANNEL) * 0.5;

  let level: 'низкое' | 'среднее' | 'высокое' | 'высшее';
  if (score < 1 / 3) {
    level = 'низкое';
  } else if (score < 2 / 3) {
    level = 'среднее';
  } else if (score < 1) {
    level = 'высокое';
  } else {
    level = 'высшее';
  }

  return {
    color: `#${normalized.toLowerCase()}`,
    label: `Качество видео: ${level}`,
  };
}
