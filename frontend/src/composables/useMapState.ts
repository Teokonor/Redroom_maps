import { ref, watch } from 'vue';
import * as d3 from 'd3';

const SHOW_INDIRECT_KEY = 'redroom:show-indirect-videos';

function readBoolean(key: string, fallback: boolean): boolean {
  if (typeof window === 'undefined') return fallback;

  try {
    const value = window.localStorage.getItem(key);
    if (value === '1') return true;
    if (value === '0') return false;
  } catch {
    // Storage can be unavailable in private mode; keep the default.
  }

  return fallback;
}

export type ProjectionId =
  | 'natural-earth'
  | 'equal-earth'
  | 'equirectangular'
  | 'mercator';

type ProjectionOption = {
  id: ProjectionId;
  label: string;
  create: () => d3.GeoProjection;
};

export const projectionOptions: ProjectionOption[] = [
  {
    id: 'natural-earth',
    label: 'Natural Earth',
    create: () => d3.geoNaturalEarth1(),
  },
  {
    id: 'equal-earth',
    label: 'Equal Earth',
    create: () => d3.geoEqualEarth(),
  },
  {
    id: 'equirectangular',
    label: 'Эквиректангулярная',
    create: () => d3.geoEquirectangular(),
  },
  {
    id: 'mercator',
    label: 'Меркатор',
    create: () => d3.geoMercator(),
  },
];

const selectedYear = ref(2025);
const isYearRulerOpen = ref(false);
const selectedProjectionId = ref<ProjectionId>('natural-earth');
const showRegionBorders = ref(false);
const showIndirectVideos = ref(readBoolean(SHOW_INDIRECT_KEY, true));
const isSettingsOpen = ref(false);

watch(showIndirectVideos, (value) => {
  if (typeof window === 'undefined') return;

  try {
    window.localStorage.setItem(SHOW_INDIRECT_KEY, value ? '1' : '0');
  } catch {
    // Ignore unavailable storage.
  }
});

export function useMapState() {
  return {
    projectionOptions,
    selectedYear,
    isYearRulerOpen,
    selectedProjectionId,
    showRegionBorders,
    showIndirectVideos,
    isSettingsOpen,
  };
}
