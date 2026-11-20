<script setup lang="ts">
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';
import { sortedYears } from '@/data/years';
import { useMobileLayout } from '@/composables/useMobileLayout';
import { formatYearHuman, formatYearTick } from '@/utils/yearLabels';
import { resolveInputYear } from '@/utils/yearInput';

type Step = 1 | 10 | 100;

const WINDOW_SIZE = 21;
const PAN_SIZE = 10;
const STEP_ORDER: Step[] = [100, 10, 1];

const props = withDefaults(
  defineProps<{
    modelValue: number;
    loading?: boolean;
    closeable?: boolean;
    collapsible?: boolean;
  }>(),
  { loading: false, closeable: false, collapsible: false }
);

const emit = defineEmits<{
  'update:modelValue': [value: number];
  close: [];
  'range-change': [
    payload: { years: number[]; step: number; selectedYear: number },
  ];
}>();

const rulerRef = ref<HTMLElement | null>(null);
const dragOffset = ref(0);
const dragging = ref(false);
let pinchStartDistance: number | null = null;
let dragLastY: number | null = null;

const TICK_HEIGHT = 20;

const isMobile = useMobileLayout();

const selectedYear = computed({
  get: () => props.modelValue,
  set: (value: number) => emit('update:modelValue', value),
});

const yearInput = ref('');

function submitYearInput() {
  const year = resolveInputYear(yearInput.value);
  yearInput.value = '';

  if (year === null) return;

  const grid = currentGrid.value;
  const targetYear = grid.includes(year)
    ? year
    : nearestYear(grid, year);

  if (targetYear !== undefined && grid.length) {
    const nextStart = centeredStart(grid, targetYear);

    if (nextStart !== windowStart.value) {
      pending.value = true;
      windowStart.value = nextStart;
    }
  }

  selectedYear.value = year;
}

const step = ref<Step>(100);
const windowStart = ref(0);
const pending = ref(false);
const collapsed = ref(false);

const currentYearLabel = computed(() => formatYearHuman(selectedYear.value));
const isCollapsed = computed(() => props.collapsible && collapsed.value);

function expandIfCollapsed() {
  if (isCollapsed.value) collapsed.value = false;
}

const locked = computed(() => props.loading || pending.value);

// Наборы лет для трёх разрешений. При приближении сохраняем более старые
// участки с прежним разрешением, а детализацию добавляем только там,
// где для неё есть отдельные карты.
const isHundredYear = (year: number) =>
  year >= -3000 &&
  year <= 2025 &&
  (year % 100 === 0 || year === 2025);

const isTenYear = (year: number) =>
  year >= -1000 &&
  year <= 2025 &&
  (year % 10 === 0 || year === 2025);

const isOneYear = (year: number) => year >= 1800 && year <= 2025;

const scaleYears: Record<Step, number[]> = {
  100: sortedYears.filter(isHundredYear),
  10: sortedYears.filter(
    (year) => isHundredYear(year) || isTenYear(year)
  ),
  1: sortedYears.filter(
    (year) => isHundredYear(year) || isTenYear(year) || isOneYear(year)
  ),
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

const canZoomIn = computed(() => finerStep.value !== null);

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
  const year = grid[index];

  if (year === undefined) return;

  // Если нужный год далеко за пределами окна (например, год остался
  // выбранным после прокрутки), центрируем окно на нём.
  if (index < start || index > end) {
    pending.value = true;

    if (index < start - 1 || index > end + 1) {
      windowStart.value = centeredStart(grid, year);
    } else {
      windowStart.value =
        index < start ? start - 1 : start + 1;
    }
  }

  selectedYear.value = year;
}

function pan(direction: number) {
  if (locked.value) return;

  const nextStart = clamp(
    windowStart.value + direction * PAN_SIZE,
    0,
    maxWindowStart.value
  );

  if (nextStart === windowStart.value) return;

  pending.value = true;
  windowStart.value = nextStart;
}

function zoomIn() {
  const nextStep = finerStep.value;
  if (locked.value || !canZoomIn.value || nextStep === null) return;

  const nextGrid = scaleYears[nextStep];
  const centerYear = nearestYear(nextGrid, selectedYear.value);

  pending.value = true;
  step.value = nextStep;
  windowStart.value = centeredStart(nextGrid, centerYear);
}

function zoomOut() {
  const nextStep = coarserStep.value;
  if (locked.value || !canZoomOut.value || nextStep === null) return;

  const nextGrid = scaleYears[nextStep];
  const centerYear = nearestYear(nextGrid, selectedYear.value);

  pending.value = true;
  step.value = nextStep;
  windowStart.value = centeredStart(nextGrid, centerYear);
}

function shiftWindow(direction: -1 | 1): boolean {
  const nextStart = clamp(
    windowStart.value + direction,
    0,
    maxWindowStart.value
  );

  if (nextStart === windowStart.value) return false;

  windowStart.value = nextStart;
  return true;
}

function pinchDistance(touches: TouchList): number {
  const first = touches[0];
  const second = touches[1];
  if (!first || !second) return 0;
  return Math.hypot(
    first.clientX - second.clientX,
    first.clientY - second.clientY
  );
}

function onTouchStart(event: TouchEvent) {
  if (event.touches.length === 2) {
    event.preventDefault();
    pinchStartDistance = pinchDistance(event.touches);
    dragLastY = null;
    dragging.value = false;
    dragOffset.value = 0;
    return;
  }

  if (event.touches.length === 1) {
    dragLastY = event.touches[0]?.clientY ?? null;
    dragOffset.value = 0;
    dragging.value = true;
  }
}

function onTouchMove(event: TouchEvent) {
  if (event.touches.length === 2 && pinchStartDistance !== null) {
    event.preventDefault();
    const distance = pinchDistance(event.touches);
    const delta = distance - pinchStartDistance;

    if (Math.abs(delta) < 40) return;

    if (delta > 0) zoomIn();
    else zoomOut();

    pinchStartDistance = distance;
    return;
  }

  if (event.touches.length !== 1 || dragLastY === null) return;

  const touch = event.touches[0];
  if (!touch) return;

  event.preventDefault();
  dragOffset.value += touch.clientY - dragLastY;
  dragLastY = touch.clientY;

  // Список едет вместе с пальцем. Когда он доходит до края окна,
  // сдвигаем само окно и меняем состав видимых лет.
  while (dragOffset.value <= -TICK_HEIGHT) {
    if (!shiftWindow(-1)) {
      dragOffset.value = 0;
      break;
    }
    dragOffset.value += TICK_HEIGHT;
  }

  while (dragOffset.value >= TICK_HEIGHT) {
    if (!shiftWindow(1)) {
      dragOffset.value = 0;
      break;
    }
    dragOffset.value -= TICK_HEIGHT;
  }
}

function onTouchEnd(event: TouchEvent) {
  if (event.touches.length < 2) pinchStartDistance = null;
  if (event.touches.length === 0) {
    dragLastY = null;
    dragging.value = false;
    dragOffset.value = 0;
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown);

  const element = rulerRef.value;
  if (!element) return;

  element.addEventListener('touchstart', onTouchStart, { passive: false });
  element.addEventListener('touchmove', onTouchMove, { passive: false });
  element.addEventListener('touchend', onTouchEnd);
  element.addEventListener('touchcancel', onTouchEnd);
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown);

  const element = rulerRef.value;
  if (!element) return;

  element.removeEventListener('touchstart', onTouchStart);
  element.removeEventListener('touchmove', onTouchMove);
  element.removeEventListener('touchend', onTouchEnd);
  element.removeEventListener('touchcancel', onTouchEnd);
});

function navigateYear(direction: -1 | 1) {
  if (locked.value) return;

  const grid = currentGrid.value;
  if (!grid.length) return;

  let index = grid.indexOf(selectedYear.value);

  if (index === -1) {
    // Выбранный год может выпадать из текущей шкалы после отдаления.
    // В таком случае берём ближайший доступный год и двигаемся от него.
    const nearest = nearestYear(grid, selectedYear.value);
    const nearestIndex = grid.indexOf(nearest);

    if (direction > 0) {
      index = nearest > selectedYear.value ? nearestIndex : nearestIndex + 1;
    } else {
      index = nearest < selectedYear.value ? nearestIndex : nearestIndex - 1;
    }
  } else {
    index += direction;
  }

  if (index < 0 || index >= grid.length) return;
  setSelectedByGridIndex(index);
}

function isKeyboardTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return true;

  if (target.closest('input, textarea, select, [contenteditable="true"]')) {
    return false;
  }

  // В прокручиваемых панелях стрелки должны листать содержимое.
  if (target.closest('.country-panel-scroll')) return false;

  return true;
}

function onKeydown(event: KeyboardEvent) {
  if (isMobile.value || event.defaultPrevented) return;
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (!isKeyboardTarget(event.target)) return;

  let direction: -1 | 1;

  if (event.key === 'ArrowUp' || event.code === 'KeyW') {
    direction = 1;
  } else if (event.key === 'ArrowDown' || event.code === 'KeyS') {
    direction = -1;
  } else {
    return;
  }

  event.preventDefault();
  navigateYear(direction);
}

function onWheel(event: WheelEvent) {
  if (locked.value) return;

  if (event.ctrlKey) {
    if (event.deltaY < 0) zoomIn();
    else if (event.deltaY > 0) zoomOut();
    return;
  }

  if (event.deltaY === 0) return;

  // Прокрутка двигает только окно лет, не меняя выбранный год.
  if (event.deltaY < 0) shiftWindow(1);
  else shiftWindow(-1);
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
    // После передачи диапазона карта сама решит, нужен ли loading.
    // Если выбранный год уже в кэше, блокировать управление незачем.
    pending.value = false;
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
    ref="rulerRef"
    class="year-ruler"
    :class="{
      'is-locked': locked,
      'is-closeable': closeable,
      'is-collapsed': isCollapsed,
    }"
    @wheel.prevent.stop="onWheel"
    @click="expandIfCollapsed"
  >
    <div v-if="collapsible" class="ruler-current">
      <button
        type="button"
        class="ruler-current-year"
        :class="{ 'is-collapsed': isCollapsed }"
        :title="isCollapsed ? 'Развернуть выбор года' : currentYearLabel"
        @click="expandIfCollapsed"
      >
        {{ currentYearLabel }}
      </button>

      <button
        v-if="!isCollapsed"
        type="button"
        class="ruler-collapse"
        title="Свернуть выбор года"
        aria-label="Свернуть выбор года"
        @click.stop="collapsed = true"
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M3 8.5 8 3.5l5 5M3 13l5-5 5 5" />
        </svg>
      </button>
    </div>

    <template v-if="!isCollapsed">
      <div v-if="collapsible" class="year-input-row">
        <input
          v-model="yearInput"
          type="text"
          inputmode="numeric"
          maxlength="6"
          class="year-input"
          placeholder="Год"
          aria-label="Ввести год"
          title="Введите год и нажмите Enter"
          @keydown.enter.prevent="submitYearInput"
        />
        <button
          type="button"
          class="year-input-apply"
          title="Применить год"
          aria-label="Применить год"
          @click="submitYearInput"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M3 8.5 6.5 12 13 4" />
          </svg>
        </button>
      </div>

      <button
        v-if="closeable"
        type="button"
        class="ruler-close"
        title="Закрыть"
        aria-label="Закрыть"
        @click="emit('close')"
      >
        <svg viewBox="0 0 12 12" aria-hidden="true">
          <path d="M2 2L10 10M10 2L2 10" />
        </svg>
      </button>

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

    <div
      class="ticks"
      :class="{ 'is-dragging': dragging }"
      :style="{ transform: `translateY(${dragOffset}px)` }"
    >
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
        <span class="tick-label">{{ formatYearTick(year) }}</span>
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
    </template>
  </aside>
</template>

<style scoped>
.year-ruler {
  position: relative;
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
  touch-action: none;
  user-select: none;
}

.year-ruler.is-closeable {
  padding-top: 34px;
}

.year-ruler.is-collapsed {
  gap: 0;
  padding-top: 8px;
  padding-bottom: 8px;
  cursor: pointer;
}

.year-ruler.is-collapsed .ruler-current {
  padding-bottom: 0;
  border-bottom: 0;
}

.ruler-current {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  width: 100%;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.year-input-row {
  display: flex;
  gap: 4px;
  width: 100%;
}

.year-input {
  flex: 1 1 auto;
  min-width: 0;
  width: 100%;
  height: 26px;
  padding: 0 6px;
  font: inherit;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: #f4f0e6;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 5px;
}

.year-input:focus {
  background: rgba(255, 216, 102, 0.1);
  border-color: #ffd866;
  outline: none;
}

.year-input::placeholder {
  color: rgba(244, 240, 230, 0.42);
}

.year-input-apply {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  color: #ffd866;
  cursor: pointer;
  background: rgba(255, 216, 102, 0.08);
  border: 1px solid rgba(255, 216, 102, 0.32);
  border-radius: 5px;
}

.year-input-apply:hover {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.year-input-apply svg {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ruler-current-year {
  flex: 0 1 auto;
  min-width: 0;
  padding: 2px;
  overflow: hidden;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
  color: #ffd866;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
  background: transparent;
  border: 0;
}

.ruler-current-year.is-collapsed {
  cursor: pointer;
}

.ruler-current-year.is-collapsed:hover {
  text-decoration: underline;
}

.ruler-collapse {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 22px;
  padding: 0;
  color: #ffd866;
  cursor: pointer;
  background: rgba(255, 216, 102, 0.08);
  border: 1px solid rgba(255, 216, 102, 0.32);
  border-radius: 4px;
}

.ruler-collapse:hover {
  background: rgba(255, 216, 102, 0.2);
  border-color: rgba(255, 216, 102, 0.6);
}

.ruler-collapse svg {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ruler-close {
  position: absolute;
  top: 6px;
  right: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
}

.ruler-close svg {
  display: block;
  width: 11px;
  height: 11px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
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
  transition: transform 0.12s ease-out;
}

.ticks.is-dragging {
  transition: none;
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
