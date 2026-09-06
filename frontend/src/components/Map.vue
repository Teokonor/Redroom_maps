<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import * as d3 from 'd3';

const svgRef = ref<SVGSVGElement | null>(null);
const mapGroupRef = ref<SVGGElement | null>(null);

const years = [1960, 1970, 1980, 1990, 2000, 2010, 2025];

const selectedYear = ref(2025);

const maps = ref<Record<number, any>>({});
const colors = ref<Record<string, string>>({});

const width = 1320;
const height = 583;

const projection = d3.geoMercator(); // Меркатор с безумной Гренландией
// const projection = d3.geoOrthographic(); // глобус
// const projection = d3.geoNaturalEarth1(); // нормальная плоская карта
// const projection = d3.geoEqualEarth(); // нормальная плоская, но слегка вытянутая вертикально
// const projection = d3.geoEquirectangular(); // нормальная плоская, ещё и абсолютно прямоугольная
const pathGenerator = d3.geoPath(projection);

const currentMap = computed(() => {
  return maps.value[selectedYear.value];
});

onMounted(async () => {
  // Загружаем цвета
  const colorsResponse = await fetch('http://127.0.0.1:8652/map/colors');
  colors.value = await colorsResponse.json();

  // Загружаем все карты
  for (const year of years) {
    const response = await fetch(`http://127.0.0.1:8652/map/geometry/${year}`);
    maps.value[year] = await response.json();
  }

  // Подгоняем проекцию под первую карту
  projection.fitSize([width, height], currentMap.value);

  const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([1, 32]).on('zoom', (event) => {
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
          v-for="country in currentMap?.features || []"
          :key="country.properties.id"
          :d="pathGenerator(country) || ''"
          :fill="colors[country.properties.colorId] || '#cccccc'"
          :stroke="colors[country.properties.colorId] || '#cccccc'"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />
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