import { computed, watch, type Ref } from 'vue';
import type { GeoProjection } from 'd3';
import {
  LABEL_FONT_FAMILY,
  LABEL_FONT_SIZE,
  LABEL_LINE_HEIGHT,
  LABEL_PADDING_X,
  LABEL_PADDING_Y,
} from '@/config/map';
import type { ProjectionId } from '@/composables/useMapState';
import {
  buildCountryLabels,
  visibleCountryLabels,
  type CountryLabel,
} from '@/utils/countryLabels';
import type { CountryFeatureCollection, LoadedMap } from '@/types/map';

export function useCountryLabels(
  currentMap: Ref<CountryFeatureCollection | undefined>,
  projection: Ref<GeoProjection>,
  selectedYear: Ref<number>,
  selectedProjectionId: Ref<ProjectionId>,
  zoomScale: Ref<number>,
  mapCache: Ref<Map<number, LoadedMap>>
) {
  // Подписи зависят от геометрии и проекции, поэтому кешируем их по году и проекции.
  const labelCache = new Map<string, CountryLabel[]>();

  function labelCacheKey(year: number): string {
    return `${selectedProjectionId.value}:${year}`;
  }

  function pruneLabelCache(yearsToKeep: number[]) {
    const prefix = `${selectedProjectionId.value}:`;
    const keep = new Set(yearsToKeep.map(labelCacheKey));

    for (const key of labelCache.keys()) {
      if (key.startsWith(prefix) && !keep.has(key)) labelCache.delete(key);
    }
  }

  const countryLabels = computed<CountryLabel[]>(() => {
    const map = currentMap.value;
    if (!map?.features?.length) return [];

    const key = labelCacheKey(selectedYear.value);
    const cached = labelCache.get(key);
    if (cached) return cached;

    const labels = buildCountryLabels(map.features, projection.value, {
      fontSize: LABEL_FONT_SIZE,
      fontFamily: LABEL_FONT_FAMILY,
      lineHeight: LABEL_LINE_HEIGHT,
      paddingX: LABEL_PADDING_X,
      paddingY: LABEL_PADDING_Y,
    });
    labelCache.set(key, labels);
    return labels;
  });

  const visibleLabels = computed(() =>
    visibleCountryLabels(countryLabels.value, zoomScale.value, {
      lineHeight: LABEL_LINE_HEIGHT,
      paddingX: LABEL_PADDING_X,
      paddingY: LABEL_PADDING_Y,
    })
  );

  watch(selectedProjectionId, () => {
    labelCache.clear();
  });

  watch(
    mapCache,
    (cache) => {
      pruneLabelCache([...cache.keys()]);
    },
    { flush: 'sync' }
  );

  return {
    visibleLabels,
  };
}
