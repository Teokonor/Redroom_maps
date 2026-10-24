<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import {
  buildCountryLabels,
  visibleCountryLabels,
  type CountryLabel,
} from '@/utils/countryLabels';
// import { years } from '@/data/years';

type CountryProperties = {
  id: string;
  colorId: string | null;
  name: string | null;
  parent: string | null;
};

const svgRef = ref<SVGSVGElement | null>(null);
const mapGroupRef = ref<SVGGElement | null>(null);

const zoomScale = ref(1);

const years = [-100, -10, 10, 0, 70, 80, 150, 180, 1862, 1863, 1930, 1941, 1945, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2025];

const selectedYear = ref(2025);

type CountryFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, CountryProperties>;

const maps = ref<Record<number, CountryFeatureCollection>>({});
const mapBorders = ref<Record<number, GeoJSON.MultiLineString>>({});
const colors = ref<Record<string, string>>({});

const width = 1320;
const height = 583;

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

// Пути считаем один раз на карту, а не при каждом зуме/рендере.
const countryShapes = computed(() => {
  const features = currentMap.value?.features;
  if (!features) return [];
  return features.map((country) => {
    const colorId = country.properties.colorId;
    return {
      id: country.properties.id,
      d: pathGenerator(country) || '',
      fill: (colorId && colors.value[colorId]) || '#cccccc',
    };
  });
});

const borderPath = computed(() =>
  currentBorders.value ? pathGenerator(currentBorders.value) || '' : ''
);

// Подписи зависят только от геометрии, поэтому кешируем их по году.
const labelCache = new Map<number, CountryLabel[]>();

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

onMounted(async () => {
  // Загружаем цвета
  const colorsResponse = await fetch('http://127.0.0.1:8652/map/colors');
  colors.value = await colorsResponse.json();

  // Загружаем все карты
  for (const year of years) {
    const response = await fetch(`http://127.0.0.1:8652/map/geometry/${year}`);
    if (!response.ok) {
      console.error(`Не удалось загрузить карту ${year}`);
      continue;
    }
    const topology = await response.json();
    const dataObject = topology.objects.data;
    if (!dataObject) {
      console.error(`В TopoJSON за ${year} нет объекта "data"`);
      continue;
    }
    // GeoJSON для заливки территорий.
    maps.value[year] = topojson.feature(
      topology,
      dataObject
    ) as unknown as CountryFeatureCollection;
    // Общие дуги между разными colorId.
    mapBorders.value[year] = topojson.mesh(
      topology,
      dataObject,
      (a, b) =>
        a === b ||
        (a.properties as CountryProperties | undefined)?.colorId !==
          (b.properties as CountryProperties | undefined)?.colorId
    );
  }
  console.log(maps)
  // Подгоняем проекцию под первую карту
  // projection.fitSize([width, height], currentMap.value);

  const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([1, 10000]).on('zoom', (event) => {
    zoomScale.value = event.transform.k;
    d3.select(mapGroupRef.value).attr('transform', event.transform)
  })
  if (!svgRef.value) return;
  d3.select(svgRef.value).call(zoom)
});
</script>

<template>
  <div style="display: flex; gap: 20px;">
    <div>
      <select v-model="selectedYear">
        <option
          v-for="year in years"
          :key="year"
          :value="year"
        >
          {{ year }}
        </option>
      </select>
    </div>

    <div>
    <svg :width="width" :height="height" ref="svgRef" class="d3-map">
      <g ref="mapGroupRef">
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
.d3-map {
  background-color: #000035;
}
</style>