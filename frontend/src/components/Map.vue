<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, watch } from 'vue';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import CountryPanel from '@/components/CountryPanel.vue';
import YearRuler from '@/components/YearRuler.vue';
import { loadCountries } from '@/api/countries';
import type { Country, CountryRegion } from '@/types/country';
import {
  buildCountryLabels,
  visibleCountryLabels,
  type CountryLabel,
} from '@/utils/countryLabels';

type CountryProperties = {
  id: string;
  colorId: string | null;
  name: string | null;
  parent: string | null;
};

const svgRef = ref<SVGSVGElement | null>(null);
const mapGroupRef = ref<SVGGElement | null>(null);

const zoomScale = ref(1);

const selectedYear = ref(2000);
const loading = ref(true);
const selectedCountryId = ref<string | null>(null);
const isCountryPanelOpen = ref(false);

watch(selectedYear, () => {
  selectedCountryId.value = null;
  isCountryPanelOpen.value = false;
});

type CountryFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, CountryProperties>;
type WorldFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry>;
type WorldVariant = 'modern' | 'ancient';
type YearRangePayload = {
  years: number[];
  step: number;
  selectedYear: number;
};
type LoadedMap = {
  year: number;
  map: CountryFeatureCollection;
  borders: GeoJSON.MultiLineString;
};

const maps = shallowRef<Record<number, CountryFeatureCollection>>({});
const mapBorders = shallowRef<Record<number, GeoJSON.MultiLineString>>({});
const colors = ref<Record<string, string>>({});
const countries = shallowRef<Country[]>([]);
const worldMaps = ref<Record<WorldVariant, WorldFeatureCollection | null>>({
  modern: null,
  ancient: null,
});

const width = 1320;
const height = 583;

const WORLD_609M_LAST_YEAR = -609;
const UNCOLORED_FILL = '#cccccc';
// colorId есть, но такого id нет в color_ids.json.
const MISSING_COLOR_FILL = '#bbbbbb';

const LABEL_FONT_SIZE = 14;
const LABEL_FONT_FAMILY = '"Segoe UI", system-ui, sans-serif';
const LABEL_LINE_HEIGHT = 12;
const LABEL_PADDING_X = 2;
const LABEL_PADDING_Y = 1;
const LABEL_STROKE_WIDTH = 1.5;

type ProjectionId =
  | 'natural-earth'
  | 'equal-earth'
  | 'equirectangular'
  | 'mercator';

type ProjectionOption = {
  id: ProjectionId;
  label: string;
  create: () => d3.GeoProjection;
};

const projectionOptions: ProjectionOption[] = [
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

const selectedProjectionId = ref<ProjectionId>('natural-earth');
const PROJECTION_PADDING = 20;

const projection = computed(() => {
  const option =
    projectionOptions.find(
      (candidate) => candidate.id === selectedProjectionId.value
    ) ?? projectionOptions[0]!;
  const nextProjection = option.create();

  nextProjection.fitExtent(
    [
      [PROJECTION_PADDING, PROJECTION_PADDING],
      [width - PROJECTION_PADDING, height - PROJECTION_PADDING],
    ],
    { type: 'Sphere' } as unknown as d3.GeoPermissibleObjects
  );

  return nextProjection;
});

const pathGenerator = computed(() => d3.geoPath(projection.value));

const currentMap = computed(() => maps.value[selectedYear.value]);
const currentBorders = computed(() => mapBorders.value[selectedYear.value]);

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
const countryShapes = computed(() => {
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

function selectCountry(id: string) {
  if (selectedCountryId.value === id) {
    if (isCountryPanelOpen.value) {
      clearSelection();
    } else {
      isCountryPanelOpen.value = true;
    }
  } else {
    selectedCountryId.value = id;
    isCountryPanelOpen.value = true;
  }

  if (selectedCountryId.value && countries.value.length === 0) {
    void ensureCountries();
  }
}

function clearSelection() {
  selectedCountryId.value = null;
  isCountryPanelOpen.value = false;
}

function closeCountryPanel() {
  isCountryPanelOpen.value = false;
}

const countriesById = computed(() => {
  const index = new Map<string, Country>();
  for (const country of countries.value) {
    index.set(country.id, country);
  }
  return index;
});

const selectedCountry = computed(() => {
  const id = selectedCountryId.value;
  return id ? countriesById.value.get(id) ?? null : null;
});

const selectedCountryShape = computed(() => {
  const id = selectedCountryId.value;
  return id
    ? countryShapes.value.find((shape) => shape.id === id) ?? null
    : null;
});

const selectedParentId = computed(() => {
  return (
    selectedCountryShape.value?.parent ??
    selectedCountry.value?.owner_id ??
    null
  );
});

const selectedParentName = computed(() => {
  const parentId = selectedParentId.value;
  if (!parentId) return null;

  return (
    countriesById.value.get(parentId)?.name ||
    selectedCountry.value?.owner?.name ||
    countryShapes.value.find((shape) => shape.id === parentId)?.name ||
    parentId
  );
});

const selectedCountryRegions = computed<CountryRegion[]>(() => {
  const rootId = selectedCountryId.value;
  if (!rootId) return [];

  return countryShapes.value
    .filter((shape) => shape.parent === rootId)
    .map((shape) => ({
      id: shape.id,
      name: countriesById.value.get(shape.id)?.name || shape.name || shape.id,
    }))
    .sort((a, b) => a.name.localeCompare(b.name, 'ru'));
});

const selectedCountryShapes = computed(() => {
  const rootId = selectedCountryId.value;
  if (!rootId) return [];

  const shapes = countryShapes.value;
  const childrenByParent = new Map<string, typeof shapes>();

  for (const shape of shapes) {
    if (!shape.parent) continue;
    const children = childrenByParent.get(shape.parent);
    if (children) children.push(shape);
    else childrenByParent.set(shape.parent, [shape]);
  }

  const selectedIds = new Set<string>([rootId]);
  const pending = [rootId];

  // Регионы могут быть вложены друг в друга, поэтому собираем всех потомков.
  while (pending.length > 0) {
    const parentId = pending.pop();
    if (parentId === undefined) continue;

    for (const child of childrenByParent.get(parentId) ?? []) {
      if (selectedIds.has(child.id)) continue;
      selectedIds.add(child.id);
      pending.push(child.id);
    }
  }

  return shapes.filter((shape) => selectedIds.has(shape.id));
});

const selectedHaloPath = computed(() =>
  selectedCountryShapes.value
    .map((shape) => shape.d)
    .filter(Boolean)
    .join(' ')
);

const borderPath = computed(() =>
  currentBorders.value ? pathGenerator.value(currentBorders.value) || '' : ''
);

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

let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null;

function resetZoom() {
  if (!svgRef.value || !zoomBehavior) return;

  d3.select(svgRef.value).call(
    zoomBehavior.transform,
    d3.zoomIdentity
  );
}

watch(selectedProjectionId, () => {
  labelCache.clear();
  resetZoom();
});

const visibleLabels = computed(() =>
  visibleCountryLabels(countryLabels.value, zoomScale.value, {
    lineHeight: LABEL_LINE_HEIGHT,
    paddingX: LABEL_PADDING_X,
    paddingY: LABEL_PADDING_Y,
  })
);

function getCountryColorId(geometry: { properties?: unknown }): string | null {
  const properties = geometry.properties as CountryProperties | undefined;
  return properties?.colorId ?? null;
}

let colorsPromise: Promise<void> | null = null;

function ensureColors() {
  if (!colorsPromise) {
    colorsPromise = (async () => {
      try {
        const response = await fetch('http://127.0.0.1:8652/map/colors', {
          cache: 'no-cache',
        });
        if (!response.ok) throw new Error('Не удалось загрузить цвета');
        colors.value = await response.json();
      } catch (error) {
        console.error('Ошибка загрузки цветов', error);
      }
    })();
  }
  return colorsPromise;
}

let countriesPromise: Promise<void> | null = null;

function ensureCountries() {
  if (!countriesPromise) {
    countriesPromise = loadCountries()
      .then((data) => {
        countries.value = data;
      })
      .catch((error) => {
        console.error('Ошибка загрузки стран', error);
        countriesPromise = null;
      });
  }
  return countriesPromise;
}

// The world files contain a single land geometry. Their feature properties
// are intentionally ignored: this is a background layer, not a country layer.
async function loadWorld(variant: WorldVariant, year: number) {
  try {
    const response = await fetch(`http://127.0.0.1:8652/map/world/${year}`);
    if (!response.ok) {
      console.error(`Не удалось загрузить подложку мира для года ${year}`);
      return;
    }
    const topology = await response.json();
    const dataObject = topology.objects.data;
    if (!dataObject) {
      console.error(`В TopoJSON подложки мира за ${year} нет объекта "data"`);
      return;
    }
    worldMaps.value[variant] = topojson.feature(
      topology,
      dataObject
    ) as unknown as WorldFeatureCollection;
  } catch (error) {
    // A missing background must not prevent the country map from loading.
    console.error(`Ошибка загрузки подложки мира для года ${year}`, error);
  }
}

async function loadMapData(year: number): Promise<LoadedMap | null> {
  try {
    const response = await fetch(`http://127.0.0.1:8652/map/geometry/${year}`, {
      cache: 'no-cache',
    });
    if (!response.ok) {
      console.error(`Не удалось загрузить карту ${year}`);
      return null;
    }

    const topology = await response.json();
    const dataObject = topology.objects.data;
    if (!dataObject) {
      console.error(`В TopoJSON за ${year} нет объекта "data"`);
      return null;
    }

    // GeoJSON для заливки территорий.
    const map = topojson.feature(
      topology,
      dataObject
    ) as unknown as CountryFeatureCollection;

    // Границы:
    // - внешние — только у цветных объектов;
    // - между двумя бесцветными — не рисуем;
    // - между бесцветным и цветным — рисуем;
    // - между цветными — только при разных colorId.
    const borders = topojson.mesh(topology, dataObject, (a, b) => {
      const aColorId = getCountryColorId(a);
      const bColorId = getCountryColorId(b);

      if (a === b) return Boolean(aColorId);
      if (!aColorId && !bColorId) return false;
      if (!aColorId || !bColorId) return true;
      return aColorId !== bColorId;
    });

    return { year, map, borders };
  } catch (error) {
    console.error(`Ошибка загрузки карты ${year}`, error);
    return null;
  }
}

let loadToken = 0;

async function loadYears(yearsToLoad: number[]) {
  const token = ++loadToken;
  loading.value = true;

  const uniqueYears = [...new Set(yearsToLoad)].sort((a, b) => a - b);
  const cachedMaps = maps.value;
  const cachedBorders = mapBorders.value;

  try {
    await ensureColors();

    const missingYears = uniqueYears.filter(
      (year) => !cachedMaps[year] || !cachedBorders[year]
    );
    const results = await Promise.all(missingYears.map(loadMapData));

    // Пока грузились новые карты, могла начаться другая загрузка.
    if (token !== loadToken) return;

    const loaded = new Map<number, LoadedMap>();
    for (const result of results) {
      if (result) loaded.set(result.year, result);
    }

    const nextMaps: Record<number, CountryFeatureCollection> = {};
    const nextBorders: Record<number, GeoJSON.MultiLineString> = {};

    for (const year of uniqueYears) {
      const loadedMap = loaded.get(year);
      if (loadedMap) {
        nextMaps[year] = loadedMap.map;
        nextBorders[year] = loadedMap.borders;
      } else if (cachedMaps[year] && cachedBorders[year]) {
        nextMaps[year] = cachedMaps[year];
        nextBorders[year] = cachedBorders[year];
      }
    }

    // Старые карты заменяются только после загрузки новых.
    maps.value = nextMaps;
    mapBorders.value = nextBorders;
    pruneLabelCache(uniqueYears);
  } finally {
    if (token === loadToken) loading.value = false;
  }
}

function handleRangeChange(range: YearRangePayload) {
  if (range.selectedYear !== selectedYear.value) {
    selectedYear.value = range.selectedYear;
  }
  void loadYears(range.years);
}

function handleMapMouseDown(event: MouseEvent) {
  // Prevent the browser's middle-click autoscroll so the map can be panned.
  if (event.button === 1) {
    event.preventDefault();
  }
}

onMounted(() => {
  void ensureColors();
  void ensureCountries();

  // Загружаем обе подложки мира: современную и для годов <= -609.
  void Promise.all([
    loadWorld('ancient', WORLD_609M_LAST_YEAR),
    loadWorld('modern', WORLD_609M_LAST_YEAR + 1),
  ]);

  zoomBehavior = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([1, 10000])
    .filter((event: MouseEvent) => {
      if (event.type === 'mousedown') {
        if (event.button === 1) return true;
        return event.button === 0 && !event.ctrlKey;
      }

      return (!event.ctrlKey || event.type === 'wheel') && !event.button;
    })
    .on('zoom', (event) => {
      zoomScale.value = event.transform.k;
      d3.select(mapGroupRef.value).attr('transform', event.transform);
    });

  if (!svgRef.value) return;
  d3.select(svgRef.value).call(zoomBehavior);
});
</script>

<template>
  <div class="map-layout">
    <YearRuler
      v-model="selectedYear"
      :loading="loading"
      @range-change="handleRangeChange"
    />

    <div class="map-stage">
      <Teleport to="#projection-slot">
        <div
          class="projection-switcher"
          role="group"
          aria-label="Проекция карты"
        >
          <span class="projection-caption">Проекция</span>
          <button
            v-for="option in projectionOptions"
            :key="option.id"
            type="button"
            class="projection-button"
            :class="{ 'is-active': selectedProjectionId === option.id }"
            @click="selectedProjectionId = option.id"
          >
            {{ option.label }}
          </button>
        </div>
      </Teleport>

      <svg
        :width="width"
        :height="height"
        ref="svgRef"
        class="d3-map"
        @click="clearSelection"
        @mousedown.capture="handleMapMouseDown"
      >
        <g ref="mapGroupRef">
          <defs>
            <mask
              id="country-selection-mask"
              maskUnits="userSpaceOnUse"
              x="0"
              y="0"
              :width="width"
              :height="height"
            >
              <rect
                x="0"
                y="0"
                :width="width"
                :height="height"
                fill="white"
              />
              <path
                v-for="country in selectedCountryShapes"
                :key="`selection-mask-${country.id}`"
                :d="country.d"
                fill="black"
              />
            </mask>
          </defs>

          <path
            v-if="worldPath"
            :d="worldPath"
            :fill="UNCOLORED_FILL"
            stroke="none"
            pointer-events="none"
          />
          <path
            v-for="country in countryShapes"
            :key="country.id"
            class="country-shape"
            :data-country-id="country.id"
            :d="country.d"
            :fill="country.fill"
            stroke="none"
            @click.stop="selectCountry(country.id)"
          />
          <path
            v-if="borderPath"
            :d="borderPath"
            fill="none"
            stroke="#222222"
            stroke-width="1"
            vector-effect="non-scaling-stroke"
            pointer-events="none"
          />
          <g
            v-if="selectedCountryShapes.length"
            class="country-selection"
            mask="url(#country-selection-mask)"
            pointer-events="none"
          >
            <path
              :d="selectedHaloPath"
              fill="none"
              stroke="#ffd866"
              stroke-opacity="0.24"
              stroke-width="27"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />
            <path
              :d="selectedHaloPath"
              fill="none"
              stroke="#ffe9a3"
              stroke-opacity="0.95"
              stroke-width="13.5"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />
          </g>
          <g
            class="country-labels"
            pointer-events="none"
            text-anchor="middle"
            dominant-baseline="central"
            :font-size="LABEL_FONT_SIZE / zoomScale"
            :stroke-width="LABEL_STROKE_WIDTH / zoomScale"
            :font-family="LABEL_FONT_FAMILY"
            fill="#ffffff"
            stroke="#000035"
            paint-order="stroke"
          >
            <text
              v-for="label in visibleLabels"
              :key="label.id"
              :transform="`translate(${label.x},${label.y}) rotate(${label.angle})`"
            >{{ label.name }}</text>
          </g>
        </g>
      </svg>

      <Transition name="country-panel">
        <CountryPanel
          v-if="selectedCountryId && isCountryPanelOpen"
          :country="selectedCountry"
          :country-id="selectedCountryId ?? ''"
          :year="selectedYear"
          :fallback-name="selectedCountryShape?.name ?? null"
          :parent-id="selectedParentId"
          :parent-name="selectedParentName"
          :regions="selectedCountryRegions"
          @close="closeCountryPanel"
          @select-country="selectCountry"
        />
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.map-layout {
  display: flex;
  align-items: center;
  gap: 20px;
}

.map-stage {
  position: relative;
  flex: 0 0 auto;
}

.projection-switcher {
  display: flex;
  align-items: center;
  width: fit-content;
  gap: 4px;
  margin: 0;
  padding: 4px 6px;
  white-space: nowrap;
  background: rgba(48, 0, 0, 0.92);
  border: 1px solid rgba(255, 216, 102, 0.36);
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
}

.projection-caption {
  padding: 0 5px;
  font-size: 10px;
  letter-spacing: 0.05em;
  color: rgba(244, 240, 230, 0.6);
  text-transform: uppercase;
}

.projection-button {
  padding: 5px 8px;
  font: inherit;
  font-size: 11px;
  line-height: 1.2;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 5px;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s;
}

.projection-button:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.36);
}

.projection-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

@media (max-width: 1100px) {
  .projection-caption {
    display: none;
  }

  .projection-button {
    padding: 4px 6px;
    font-size: 10px;
  }
}

.d3-map {
  display: block;
  background-color: #000035;
  cursor: default;
}

.country-panel-enter-active,
.country-panel-leave-active {
  transition:
    transform 0.22s ease,
    opacity 0.22s ease;
}

.country-panel-enter-from,
.country-panel-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>