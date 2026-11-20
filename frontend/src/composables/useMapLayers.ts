import { computed, ref, shallowRef, watch, type Ref } from 'vue';
import * as d3 from 'd3';
import { fetchMapResource } from '@/api/maps';
import {
  MAP_CACHE_LIMITS,
  MISSING_COLOR_FILL,
  PROJECTION_PADDING,
  UNCOLORED_FILL,
  WORLD_609M_LAST_YEAR,
  MAP_HEIGHT,
  MAP_WIDTH,
} from '@/config/map';
import { projectionOptions, type ProjectionId } from '@/composables/useMapState';
import { useMobileLayout } from '@/composables/useMobileLayout';
import type {
  CountryShape,
  LoadedMap,
  WorldFeatureCollection,
  WorldVariant,
  YearRangePayload,
} from '@/types/map';
import { parseMapTopology, parseWorldTopology } from '@/utils/mapGeometry';

export function useMapLayers(
  selectedYear: Ref<number>,
  selectedProjectionId: Ref<ProjectionId>
) {
  const isMobile = useMobileLayout();

  const loading = ref(true);
  const colors = ref<Record<string, string>>({});
  const currentStep = ref(100);

  const mapCache = shallowRef(new Map<number, LoadedMap>());
  const mapCacheOrder: number[] = [];
  const pendingMaps = new Map<number, Promise<LoadedMap | null>>();

  const worldMaps = ref<Record<WorldVariant, WorldFeatureCollection | null>>({
    modern: null,
    ancient: null,
  });
  const worldPromises = new Map<WorldVariant, Promise<void>>();

  let selectedRequest = 0;
  let prefetchGeneration = 0;
  let latestRange: YearRangePayload | null = null;
  let initialized = false;

  const projection = computed(() => {
    const option =
      projectionOptions.find(
        (candidate) => candidate.id === selectedProjectionId.value
      ) ?? projectionOptions[0]!;
    const nextProjection = option.create();

    nextProjection.fitExtent(
      [
        [PROJECTION_PADDING, PROJECTION_PADDING],
        [MAP_WIDTH - PROJECTION_PADDING, MAP_HEIGHT - PROJECTION_PADDING],
      ],
      { type: 'Sphere' } as unknown as d3.GeoPermissibleObjects
    );

    return nextProjection;
  });

  const pathGenerator = computed(() => d3.geoPath(projection.value));

  const currentMap = computed(
    () => mapCache.value.get(selectedYear.value)?.map
  );
  const currentBorders = computed(
    () => mapCache.value.get(selectedYear.value)?.borders
  );
  const currentRegionBorders = computed(
    () => mapCache.value.get(selectedYear.value)?.regionBorders
  );

  function worldVariantForYear(year: number): WorldVariant {
    return year <= WORLD_609M_LAST_YEAR ? 'ancient' : 'modern';
  }

  const currentWorld = computed(
    () => worldMaps.value[worldVariantForYear(selectedYear.value)]
  );

  const worldPath = computed(() =>
    currentWorld.value ? pathGenerator.value(currentWorld.value) || '' : ''
  );

  // Пути считаем один раз на карту, а не при каждом зуме/рендере.
  const countryShapes = computed<CountryShape[]>(() => {
    const features = currentMap.value?.features;
    if (!features) return [];

    return features.map((country) => {
      const colorId = country.properties.colorId;

      return {
        id: country.properties.id,
        parent: country.properties.parent,
        name: country.properties.name,
        d: pathGenerator.value(country) || '',
        fill: colorId
          ? colors.value[colorId] ?? MISSING_COLOR_FILL
          : UNCOLORED_FILL,
      };
    });
  });

  const borderPath = computed(() =>
    currentBorders.value
      ? pathGenerator.value(currentBorders.value) || ''
      : ''
  );

  const regionBorderPath = computed(() =>
    currentRegionBorders.value
      ? pathGenerator.value(currentRegionBorders.value) || ''
      : ''
  );

  function cacheLimit(): number {
    if (isMobile.value) return 4;
    return MAP_CACHE_LIMITS[currentStep.value] ?? 41;
  }

  function touchMap(year: number) {
    const index = mapCacheOrder.indexOf(year);
    if (index >= 0) mapCacheOrder.splice(index, 1);
    mapCacheOrder.push(year);
  }

  function pruneMaps() {
    const limit = cacheLimit();
    if (mapCache.value.size <= limit) return;

    const next = new Map(mapCache.value);
    while (next.size > limit) {
      const oldest = mapCacheOrder.shift();
      if (oldest === undefined) break;
      if (oldest === selectedYear.value) {
        mapCacheOrder.push(oldest);
        break;
      }
      next.delete(oldest);
    }

    mapCache.value = next;
  }

  function storeMap(loaded: LoadedMap) {
    const next = new Map(mapCache.value);
    next.set(loaded.year, loaded);
    mapCache.value = next;
    touchMap(loaded.year);
    pruneMaps();
  }

  let colorsPromise: Promise<void> | null = null;

  function ensureColors() {
    if (!colorsPromise) {
      colorsPromise = (async () => {
        try {
          const response = await fetchMapResource('/map/colors');
          if (!response.ok) throw new Error('Не удалось загрузить цвета');
          colors.value = await response.json();
        } catch (error) {
          console.error('Ошибка загрузки цветов', error);
        }
      })();
    }
    return colorsPromise;
  }

  // The world files contain a single land geometry. Their feature properties
  // are intentionally ignored: this is a background layer, not a country layer.
  async function loadWorldData(variant: WorldVariant, year: number) {
    try {
      const response = await fetchMapResource(`/map/world/${year}`);
      if (!response.ok) {
        console.error(`Не удалось загрузить подложку мира для года ${year}`);
        return;
      }

      const topology = await response.json();
      const world = parseWorldTopology(topology);

      if (!world) {
        console.error(
          `В TopoJSON подложки мира за ${year} нет объекта "data"`
        );
        return;
      }

      worldMaps.value[variant] = world;
    } catch (error) {
      // A missing background must not prevent the country map from loading.
      console.error(`Ошибка загрузки подложки мира для года ${year}`, error);
    }
  }

  function ensureWorld(variant: WorldVariant, year: number): Promise<void> {
    if (worldMaps.value[variant]) return Promise.resolve();

    const pending = worldPromises.get(variant);
    if (pending) return pending;

    const promise = loadWorldData(variant, year).finally(() => {
      worldPromises.delete(variant);
    });
    worldPromises.set(variant, promise);
    return promise;
  }

  async function loadMapData(year: number): Promise<LoadedMap | null> {
    try {
      const response = await fetchMapResource(`/map/geometry/${year}`);
      if (!response.ok) {
        console.error(`Не удалось загрузить карту ${year}`);
        return null;
      }

      const topology = await response.json();
      const loaded = parseMapTopology(topology, year);

      if (!loaded) {
        console.error(`В TopoJSON за ${year} нет объекта "data"`);
        return null;
      }

      return loaded;
    } catch (error) {
      console.error(`Ошибка загрузки карты ${year}`, error);
      return null;
    }
  }

  function loadMap(year: number): Promise<LoadedMap | null> {
    const cached = mapCache.value.get(year);
    if (cached) {
      touchMap(year);
      return Promise.resolve(cached);
    }

    const pending = pendingMaps.get(year);
    if (pending) return pending;

    const promise = loadMapData(year)
      .then((loaded) => {
        if (loaded) storeMap(loaded);
        return loaded;
      })
      .finally(() => {
        pendingMaps.delete(year);
      });

    pendingMaps.set(year, promise);
    return promise;
  }

  async function ensureSelectedMap(year: number) {
    const request = ++selectedRequest;
    const cached = mapCache.value.get(year);
    if (cached) {
      touchMap(year);
      loading.value = false;
      return;
    }

    loading.value = true;
    const loaded = await loadMap(year);
    if (request !== selectedRequest) return;
    if (loaded) touchMap(year);
    loading.value = false;
  }

  async function prefetchRange(years: number[], selected: number) {
    const generation = ++prefetchGeneration;
    const limit = isMobile.value ? 2 : 4;

    // Предзагружаем только ближайшие карты. Остальные уже загруженные
    // карты остаются в кэше, но спекулятивно их больше не качаем.
    const missing = years
      .filter((year) => year !== selected && !mapCache.value.has(year))
      .sort(
        (left, right) =>
          Math.abs(left - selected) - Math.abs(right - selected)
      )
      .slice(0, limit);

    // По три карты за раз, чтобы не занимать все соединения браузера
    // и оставить место для карты, которую пользователь выберет вручную.
    for (let index = 0; index < missing.length; index += 3) {
      const batch = missing.slice(index, index + 3);
      await Promise.all(batch.map((year) => loadMap(year)));
      if (generation !== prefetchGeneration) return;
    }
  }

  async function applyRange(range: YearRangePayload) {
    currentStep.value = range.step;
    pruneMaps();

    if (range.selectedYear !== selectedYear.value) {
      selectedYear.value = range.selectedYear;
    }

    // Сначала показываем выбранный год, только потом догружаем остальные.
    await ensureSelectedMap(range.selectedYear);
    await prefetchRange(range.years, range.selectedYear);
  }

  function handleRangeChange(range: YearRangePayload) {
    latestRange = range;
    if (!initialized) return;
    void applyRange(range);
  }

  watch(selectedYear, (year) => {
    if (!initialized) return;

    void ensureSelectedMap(year);

    const variant = worldVariantForYear(year);
    void ensureWorld(
      variant,
      variant === 'ancient'
        ? WORLD_609M_LAST_YEAR
        : WORLD_609M_LAST_YEAR + 1
    );
  });

  async function initialize() {
    // Порядок: цвета, актуальная подложка, выбранная карта,
    // остальные карты диапазона, древняя подложка.
    await ensureColors();
    await ensureWorld('modern', WORLD_609M_LAST_YEAR + 1);

    initialized = true;
    if (latestRange) {
      await applyRange(latestRange);
    } else {
      await ensureSelectedMap(selectedYear.value);
    }

    if (!isMobile.value) {
      await ensureWorld('ancient', WORLD_609M_LAST_YEAR);
    }
  }

  return {
    loading,
    projection,
    mapCache,
    currentMap,
    worldPath,
    countryShapes,
    borderPath,
    regionBorderPath,
    handleRangeChange,
    initialize,
  };
}
