<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { years as allYears } from '@/data/years';

type Step = 1 | 10 | 100;

const WINDOW_SIZE = 21;
const PAN_SIZE = 10;
const STEP_ORDER: Step[] = [100, 10, 1];

const props = withDefaults(
  defineProps<{
    modelValue: number;
    loading?: boolean;
  }>(),
  { loading: false }
);

const emit = defineEmits<{
  'update:modelValue': [value: number];
  'range-change': [
    payload: { years: number[]; step: number; selectedYear: number },
  ];
}>();

const selectedYear = computed({
  get: () => props.modelValue,
  set: (value: number) => emit('update:modelValue', value),
});

const step = ref<Step>(100);
const windowStart = ref(0);
const pending = ref(false);

const locked = computed(() => props.loading || pending.value);

const sortedYears = [...allYears].sort((a, b) => a - b);

// Наборы лет для трёх разрешений. Ограничения повторяют плотность данных
// в data/years.ts: 100 лет — -3000..2000, 10 лет — -1000..2025, 1 год — 1800..2000.
const scaleYears: Record<Step, number[]> = {
  100: sortedYears.filter(
    (year) => year >= -3000 && year <= 2000 && year % 100 === 0
  ),
  10: sortedYears.filter(
    (year) =>
      year >= -1000 &&
      year <= 2025 &&
      (year % 10 === 0 || year === 2025)
  ),
  1: sortedYears.filter((year) => year >= 1800 && year <= 2000),
};

const currentGrid = computed(() => scaleYears[step.value]);

const maxWindowStart = computed(() =>
  Math.max(0, currentGrid.value.length - WINDOW_SIZE)
);

const visibleYearsAsc = computed(() =>
  currentGrid.value.slice(windowStart.value, windowStart.value + WINDOW_SIZE)
);

const displayYears = computed(() => [...visibleYearsAsc.value].reverse());

const stepLabel = computed(() =>
  step.value === 1 ? 'каждый год' : `каждые ${step.value} лет`
);

const stepIndex = computed(() => STEP_ORDER.indexOf(step.value));

const finerStep = computed<Step | null>(
  () => STEP_ORDER[stepIndex.value + 1] ?? null
);

const coarserStep = computed<Step | null>(
  () => STEP_ORDER[stepIndex.value - 1] ?? null
);

const canZoomIn = computed(
  () =>
    finerStep.value !== null &&
    scaleYears[finerStep.value].includes(selectedYear.value)
);

const canZoomOut = computed(() => coarserStep.value !== null);

const canPanUp = computed(() => windowStart.value < maxWindowStart.value);
const canPanDown = computed(() => windowStart.value > 0);

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function centeredStart(grid: number[], year: number) {
  const index = grid.indexOf(year);
  if (index === -1) return 0;
  return clamp(
    index - Math.floor(WINDOW_SIZE / 2),
    0,
    Math.max(0, grid.length - WINDOW_SIZE)
  );
}

function nearestYear(grid: number[], year: number) {
  return grid.reduce((best, current) => {
    const bestDistance = Math.abs(best - year);
    const currentDistance = Math.abs(current - year);

    if (currentDistance < bestDistance) return current;
    if (currentDistance === bestDistance && current > best) return current;
    return best;
  }, grid[0] ?? year);
}

function selectYear(year: number) {
  if (locked.value) return;
  selectedYear.value = year;
}

function setSelectedByGridIndex(index: number) {
  const grid = currentGrid.value;
  if (index < 0 || index >= grid.length) return;

  const start = windowStart.value;
  const end = start + visibleYearsAsc.value.length - 1;

  // При скролле у края списка сдвигаем окно на одну позицию,
  // чтобы можно было продолжать листать годы без смены масштаба.
  if (index < start) {
    pending.value = true;
    windowStart.value = start - 1;
  } else if (index > end) {
    pending.value = true;
    windowStart.value = start + 1;
  }

  const year = grid[index];
  if (year === undefined) return;
  selectedYear.value = year;
}

function pan(direction: number) {
  if (locked.value) return;

  const grid = currentGrid.value;
  const nextStart = clamp(
    windowStart.value + direction * PAN_SIZE,
    0,
    maxWindowStart.value
  );

  if (nextStart === windowStart.value) return;

  pending.value = true;
  windowStart.value = nextStart;

  const nextVisible = grid.slice(nextStart, nextStart + WINDOW_SIZE);
  const oldest = nextVisible[0];
  const newest = nextVisible[nextVisible.length - 1];

  if (oldest === undefined || newest === undefined) return;
  if (selectedYear.value < oldest) selectedYear.value = oldest;
  else if (selectedYear.value > newest) selectedYear.value = newest;
}

function zoomIn() {
  const nextStep = finerStep.value;
  if (locked.value || !canZoomIn.value || nextStep === null) return;

  pending.value = true;
  step.value = nextStep;
  windowStart.value = centeredStart(
    scaleYears[nextStep],
    selectedYear.value
  );
}

function zoomOut() {
  const nextStep = coarserStep.value;
  if (locked.value || !canZoomOut.value || nextStep === null) return;

  const targetYear = nearestYear(
    scaleYears[nextStep],
    selectedYear.value
  );

  pending.value = true;
  step.value = nextStep;
  selectedYear.value = targetYear;
  windowStart.value = centeredStart(scaleYears[nextStep], targetYear);
}

function onWheel(event: WheelEvent) {
  if (locked.value) return;

  if (event.ctrlKey) {
    if (event.deltaY < 0) zoomIn();
    else if (event.deltaY > 0) zoomOut();
    return;
  }

  if (event.deltaY === 0) return;

  const index = currentGrid.value.indexOf(selectedYear.value);
  if (index === -1) return;

  setSelectedByGridIndex(index + (event.deltaY < 0 ? 1 : -1));
}

windowStart.value = centeredStart(scaleYears[step.value], props.modelValue);

watch(
  () => `${step.value}:${visibleYearsAsc.value.join(',')}`,
  () => {
    emit('range-change', {
      years: [...visibleYearsAsc.value],
      step: step.value,
      selectedYear: selectedYear.value,
    });
  },
  { immediate: true }
);

watch(
  () => props.loading,
  (loading) => {
    if (!loading) pending.value = false;
  }
);
</script>

<template>
  <aside
    class="year-ruler"
    :class="{ 'is-locked': locked }"
    @wheel.prevent.stop="onWheel"
  >
    <div class="ruler-top">
      <div class="zoom-controls">
        <button
          type="button"
          class="icon-button"
          title="Приблизить"
          :disabled="locked || !canZoomIn"
          @click="zoomIn"
        >
          +
        </button>
        <button
          type="button"
          class="icon-button"
          title="Отдалить"
          :disabled="locked || !canZoomOut"
          @click="zoomOut"
        >
          −
        </button>
      </div>
      <div class="scale-label">{{ stepLabel }}</div>
    </div>

    <button
      type="button"
      class="pan-button"
      title="Вверх — к более новым годам"
      :disabled="locked || !canPanUp"
      @click="pan(1)"
    >
      ▲
    </button>

    <div class="ticks">
      <button
        v-for="year in displayYears"
        :key="year"
        type="button"
        class="tick"
        :class="{ active: year === selectedYear }"
        :disabled="locked"
        @click="selectYear(year)"
      >
        <span class="tick-mark" />
        <span class="tick-label">{{ year }}</span>
      </button>
    </div>

    <button
      type="button"
      class="pan-button"
      title="Вниз — к более древним годам"
      :disabled="locked || !canPanDown"
      @click="pan(-1)"
    >
      ▼
    </button>

    <div class="loading" :class="{ visible: locked }">Загрузка…</div>
  </aside>
</template>

<style scoped>
.year-ruler {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  width: 128px;
  padding: 10px 9px;
  color: #e8e8e8;
  background: rgba(0, 0, 53, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 10px;
  user-select: none;
}

.year-ruler.is-locked {
  cursor: wait;
}

.ruler-top {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  width: 100%;
}

.zoom-controls {
  display: flex;
  gap: 6px;
}

.icon-button,
.pan-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #f4f4f4;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 5px;
  cursor: pointer;
  transition:
    background-color 0.15s,
    border-color 0.15s,
    opacity 0.15s;
}

.icon-button {
  width: 32px;
  height: 27px;
  font-size: 18px;
  line-height: 1;
}

.pan-button {
  width: 100%;
  height: 23px;
  font-size: 11px;
}

.icon-button:hover:not(:disabled),
.pan-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.45);
}

.icon-button:disabled,
.pan-button:disabled {
  opacity: 0.28;
  cursor: default;
}

.scale-label {
  font-size: 10px;
  letter-spacing: 0.02em;
  color: rgba(255, 255, 255, 0.62);
  white-space: nowrap;
}

.ticks {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 2px 0 2px 14px;
}

.ticks::before {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 7px;
  width: 1px;
  content: '';
  background: rgba(255, 255, 255, 0.28);
}

.tick {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 20px;
  padding: 0 3px;
  font: inherit;
  color: inherit;
  text-align: left;
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.tick:disabled {
  cursor: default;
}

.tick:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
}

.tick-mark {
  flex: 0 0 10px;
  width: 10px;
  height: 1px;
  background: rgba(255, 255, 255, 0.5);
}

.tick-label {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.tick.active {
  color: #ffd866;
  background: rgba(255, 216, 102, 0.14);
  box-shadow: inset 2px 0 0 #ffd866;
}

.tick.active .tick-mark {
  background: #ffd866;
}

.loading {
  height: 13px;
  font-size: 10px;
  line-height: 13px;
  color: #ffd866;
  opacity: 0;
  transition: opacity 0.15s;
}

.loading.visible {
  opacity: 1;
}
</style>
