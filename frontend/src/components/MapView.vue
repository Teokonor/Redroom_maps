<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import CountryPanel from '@/components/CountryPanel.vue';
import YearRuler from '@/components/YearRuler.vue';
import {
  LABEL_FONT_FAMILY,
  LABEL_FONT_SIZE,
  LABEL_STROKE_WIDTH,
  MAP_HEIGHT as height,
  MAP_WIDTH as width,
  UNCOLORED_FILL,
} from '@/config/map';
import { useCountryLabels } from '@/composables/useCountryLabels';
import { useCountrySelection } from '@/composables/useCountrySelection';
import { useMapLayers } from '@/composables/useMapLayers';
import { useMapState } from '@/composables/useMapState';
import { useMapViewport } from '@/composables/useMapViewport';
import { useMapZoom } from '@/composables/useMapZoom';
import { useMobileLayout } from '@/composables/useMobileLayout';

const svgRef = ref<SVGSVGElement | null>(null);
const mapGroupRef = ref<SVGGElement | null>(null);
const mapLayoutRef = ref<HTMLElement | null>(null);
const rulerWrapRef = ref<HTMLElement | null>(null);

const isMobile = useMobileLayout();
const {
  projectionOptions,
  selectedYear,
  isYearRulerOpen,
  selectedProjectionId,
  showRegionBorders,
} = useMapState();

const {
  loading,
  projection,
  mapCache,
  currentMap,
  worldPath,
  countryShapes,
  borderPath,
  regionBorderPath,
  handleRangeChange,
  initialize: initializeMap,
} = useMapLayers(selectedYear, selectedProjectionId);

const { zoomScale, mapRenderKey, resetZoom } = useMapZoom(
  svgRef,
  mapGroupRef
);

const { visibleLabels } = useCountryLabels(
  currentMap,
  projection,
  selectedYear,
  selectedProjectionId,
  zoomScale,
  mapCache
);

const {
  selectedCountryId,
  isCountryPanelOpen,
  selectCountry,
  clearSelection,
  closeCountryPanel,
  selectedCountry,
  selectedCountryShape,
  selectedParentId,
  selectedParentName,
  selectedCountryRegions,
  selectedCountryShapes,
  selectedHaloPath,
} = useCountrySelection(selectedYear, countryShapes);

const {
  rulerDragging,
  rulerStyle,
  startRulerDrag,
  handleRulerClickCapture,
} = useMapViewport(mapLayoutRef, rulerWrapRef);

watch(selectedProjectionId, () => {
  resetZoom();
});

function handleMapMouseDown(event: MouseEvent) {
  // Prevent the browser's middle-click autoscroll so the map can be panned.
  if (event.button === 1) {
    event.preventDefault();
  }
}

function handleMapKeydown(event: KeyboardEvent) {
  if (!isMobile.value || event.key !== 'Escape') return;
  if (
    document.querySelector(
      '.video-details-backdrop, .periods-backdrop, .mobile-menu, ' +
        '.mobile-settings-backdrop, .top-panel'
    )
  ) {
    return;
  }

  if (isCountryPanelOpen.value) {
    clearSelection();
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleMapKeydown);
  void initializeMap().catch((error) => {
    console.error('Ошибка инициализации карты', error);
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleMapKeydown);
});
</script>

<template>
  <div ref="mapLayoutRef" class="map-layout">
    <div
      v-show="!isMobile || isYearRulerOpen"
      ref="rulerWrapRef"
      class="year-ruler-wrap"
      :class="{ 'is-dragging': rulerDragging }"
      :style="rulerStyle"
      @pointerdown="startRulerDrag"
      @click.capture="handleRulerClickCapture"
    >
      <YearRuler
        v-model="selectedYear"
        :loading="loading"
        :closeable="isMobile"
        :collapsible="!isMobile"
        @close="isYearRulerOpen = false"
        @range-change="handleRangeChange"
      />
    </div>

    <div class="map-stage">
      <Teleport to="#projection-slot">
        <div class="map-controls">
          <label class="region-borders-toggle">
            <input
              v-model="showRegionBorders"
              type="checkbox"
              class="region-borders-checkbox"
            />
            <span>Границы регионов</span>
          </label>

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
        </div>
      </Teleport>

      <svg
        :width="width"
        :height="height"
        :viewBox="`0 0 ${width} ${height}`"
        preserveAspectRatio="xMidYMid meet"
        ref="svgRef"
        class="d3-map"
        @click="clearSelection"
        @mousedown.capture="handleMapMouseDown"
      >
        <g ref="mapGroupRef" :key="mapRenderKey">
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
          <path
            v-if="showRegionBorders && regionBorderPath"
            class="region-borders"
            :d="regionBorderPath"
            fill="none"
            stroke="#222222"
            stroke-width="0.6"
            stroke-dasharray="3 3"
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
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
}

.year-ruler-wrap {
  position: absolute;
  top: 50%;
  left: 16px;
  z-index: 20;
  width: 128px;
  max-height: calc(100% - 32px);
  transform: translateY(-50%);
}

.year-ruler-wrap :deep(.year-ruler) {
  max-height: 100%;
}

.year-ruler-wrap :deep(.ruler-current) {
  cursor: grab;
}

.year-ruler-wrap.is-dragging,
.year-ruler-wrap.is-dragging :deep(.ruler-current) {
  cursor: grabbing;
}

.year-ruler-wrap :deep(.ticks) {
  flex: 0 1 auto;
  min-height: 0;
  overflow-y: auto;
}

.map-stage {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000035;
}

.map-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.region-borders-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  font-size: 11px;
  line-height: 1.2;
  color: #f4f0e6;
  white-space: nowrap;
  cursor: pointer;
  background: rgba(48, 0, 0, 0.92);
  border: 1px solid rgba(255, 216, 102, 0.36);
  border-radius: 8px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  transition: border-color 0.15s;
}

.region-borders-toggle:hover {
  border-color: rgba(255, 216, 102, 0.7);
}

.region-borders-checkbox {
  width: 13px;
  height: 13px;
  margin: 0;
  cursor: pointer;
  accent-color: #ffd866;
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
  width: 100%;
  height: 100%;
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

@media (max-width: 600px) {
  .map-layout {
    position: relative;
    display: block;
    height: 100%;
  }

  .map-stage {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #000035;
  }

  .year-ruler-wrap {
    position: absolute;
    top: 50%;
    left: 8px;
    z-index: 20;
    width: 104px;
    height: auto;
    max-height: calc(100% - 16px);
    transform: translateY(-50%);
  }

  .year-ruler-wrap :deep(.year-ruler) {
    width: 100%;
    height: auto;
    max-height: 100%;
    gap: 3px;
  }

  .year-ruler-wrap :deep(.ticks) {
    flex: 0 1 auto;
    min-height: 0;
    overflow-y: auto;
  }

  .d3-map {
    position: absolute;
    top: 0;
    left: 50%;
    width: auto;
    height: 100%;
    max-width: none;
    transform: translateX(-50%);
  }
}
</style>