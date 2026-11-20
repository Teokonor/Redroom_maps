import { ref } from 'vue';
import * as d3 from 'd3';

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
const isSettingsOpen = ref(false);

export function useMapState() {
  return {
    projectionOptions,
    selectedYear,
    isYearRulerOpen,
    selectedProjectionId,
    showRegionBorders,
    isSettingsOpen,
  };
}
