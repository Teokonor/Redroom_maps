<script setup lang="ts">
import { ref, shallowRef, computed, onMounted } from 'vue';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import YearRuler from '@/components/YearRuler.vue';
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

// const projection = d3.geoMercator(); // Меркатор с безумной Гренландией
// const projection = d3.geoOrthographic(); // глобус
const projection = d3.geoNaturalEarth1(); // нормальная плоская карта
// const projection = d3.geoEqualEarth(); // нормальная плоская, но слегка вытянутая вертикально
// const projection = d3.geoEquirectangular(); // нормальная плоская, ещё и абсолютно прямоугольная
const pathGenerator = d3.geoPath(projection);

const currentMap = computed(() => maps.value[selectedYear.value]);
const currentBorders = computed(() => mapBorders.value[selectedYear.value]);

function worldVariantForYear(year: number): WorldVariant {
  return year <= WORLD_609M_LAST_YEAR ? 'ancient' : 'modern';
}

const currentWorld = computed(
  () => worldMaps.value[worldVariantForYear(selectedYear.value)]
);

const worldPath = computed(() =>
  currentWorld.value ? pathGenerator(currentWorld.value) || '' : ''
);

// Пути считаем один раз на карту, а не при каждом зуме/рендере.
const countryShapes = computed(() => {
  const features = currentMap.value?.features;
  if (!features) return [];
  return features.map((country) => {
    const colorId = country.properties.colorId;
    return {
      id: country.properties.id,
      d: pathGenerator(country) || '',
      fill: colorId
        ? colors.value[colorId] ?? MISSING_COLOR_FILL
        : UNCOLORED_FILL,
    };
  });
});

const borderPath = computed(() =>
  currentBorders.value ? pathGenerator(currentBorders.value) || '' : ''
);

// Подписи зависят только от геометрии, поэтому кешируем их по году.
const labelCache = new Map<number, CountryLabel[]>();

function pruneLabelCache(yearsToKeep: number[]) {
  const keep = new Set(yearsToKeep);
  for (const year of labelCache.keys()) {
    if (!keep.has(year)) labelCache.delete(year);
  }
}

const countryLabels = computed<CountryLabel[]>(() => {
  const map = currentMap.value;
  if (!map?.features?.length) return [];

  const cached = labelCache.get(selectedYear.value);
  if (cached) return cached;

  const labels = buildCountryLabels(map.features, projection, {
    fontSize: LABEL_FONT_SIZE,
    fontFamily: LABEL_FONT_FAMILY,
    lineHeight: LABEL_LINE_HEIGHT,
    paddingX: LABEL_PADDING_X,
    paddingY: LABEL_PADDING_Y,
  });
  labelCache.set(selectedYear.value, labels);
  return labels;
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
        const response = await fetch('http://127.0.0.1:8652/map/colors');
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
    const response = await fetch(`http://127.0.0.1:8652/map/geometry/${year}`);
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

onMounted(() => {
  void ensureColors();

  // Загружаем обе подложки мира: современную и для годов <= -609.
  void Promise.all([
    loadWorld('ancient', WORLD_609M_LAST_YEAR),
    loadWorld('modern', WORLD_609M_LAST_YEAR + 1),
  ]);

  const zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([1, 10000])
    .on('zoom', (event) => {
      zoomScale.value = event.transform.k;
      d3.select(mapGroupRef.value).attr('transform', event.transform);
    });

  if (!svgRef.value) return;
  d3.select(svgRef.value).call(zoom);
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
      <svg :width="width" :height="height" ref="svgRef" class="d3-map">
        <g ref="mapGroupRef">
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
            :d="country.d"
            :fill="country.fill"
            stroke="none"
          />
          <path
            v-if="borderPath"
            :d="borderPath"
            fill="none"
            stroke="#222222"
            stroke-width="1"
            vector-effect="non-scaling-stroke"
          />
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
  flex: 0 0 auto;
}

.d3-map {
  background-color: #000035;
}
</style>