export const MAP_WIDTH = 1320;
export const MAP_HEIGHT = 583;

export const WORLD_609M_LAST_YEAR = -609;

export const UNCOLORED_FILL = '#cccccc';
// colorId есть, но такого id нет в color_ids.json.
export const MISSING_COLOR_FILL = '#bbbbbb';

// Ограничения кэша заданы в количестве карт на текущий масштаб.
// 100-летний масштаб целиком помещается в память; для 10/1 лет
// храним текущее окно и соседние карты.
export const MAP_CACHE_LIMITS: Record<number, number> = {
  100: 51,
  10: 41,
  1: 41,
};

export const LABEL_FONT_SIZE = 14;
export const LABEL_FONT_FAMILY = '"Segoe UI", system-ui, sans-serif';
export const LABEL_LINE_HEIGHT = 12;
export const LABEL_PADDING_X = 2;
export const LABEL_PADDING_Y = 1;
export const LABEL_STROKE_WIDTH = 1.5;

export const PROJECTION_PADDING = 20;

export const MAP_RENDER_REFRESH_MS = 60_000;
