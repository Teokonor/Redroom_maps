<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import type { Country } from '@/types/country';
import type { PeriodRow, VideoPeriod } from '@/types/period';
import type { Video } from '@/types/video';
import PeriodsTable from '@/components/PeriodsTable.vue';
import { loadCountries } from '@/api/countries';
import { loadVideoPeriods } from '@/api/videos';
import { useMapState } from '@/composables/useMapState';

const props = defineProps<{
  video: Video;
}>();

const emit = defineEmits<{
  close: [];
}>();

const titleId = computed(() => `video-periods-title-${props.video.num}`);

const { showIndirectVideos } = useMapState();

const periods = ref<VideoPeriod[]>([]);
const countries = ref<Country[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const closeButton = ref<HTMLButtonElement | null>(null);
let requestId = 0;

const countriesById = computed(() => {
  const index = new Map<string, string>();
  for (const country of countries.value) {
    index.set(country.id, country.name);
  }
  return index;
});

function buildRows(items: VideoPeriod[]): PeriodRow[] {
  return items.map((period) => ({
    countryId: period.country_id,
    countryName:
      countriesById.value.get(period.country_id) ?? period.country_id,
    beginYear: period.begin_year,
    endYear: period.end_year,
  }));
}

const mainRows = computed(() =>
  buildRows(periods.value.filter((period) => period.is_main))
);

const indirectRows = computed(() =>
  buildRows(periods.value.filter((period) => !period.is_main))
);

const hasPeriods = computed(
  () =>
    mainRows.value.length > 0 ||
    (showIndirectVideos.value && indirectRows.value.length > 0)
);

const emptyMessage = computed(() => {
  if (
    !showIndirectVideos.value &&
    mainRows.value.length === 0 &&
    indirectRows.value.length > 0
  ) {
    return 'У этого видео нет основной темы';
  }

  return 'У этого видео нет периодов';
});

async function load() {
  const current = ++requestId;
  loading.value = true;
  error.value = null;

  try {
    const [nextPeriods, nextCountries] = await Promise.all([
      loadVideoPeriods(props.video.num),
      loadCountries(),
    ]);

    if (current !== requestId) return;

    periods.value = nextPeriods;
    countries.value = nextCountries;
  } catch (caught) {
    if (current !== requestId) return;

    error.value =
      caught instanceof Error
        ? caught.message
        : 'Не удалось загрузить периоды';
  } finally {
    if (current === requestId) loading.value = false;
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.stopPropagation();
    emit('close');
  }
}

watch(
  () => props.video.num,
  () => {
    void load();
  }
);

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);
  closeButton.value?.focus();
  void load();
});

onBeforeUnmount(() => {
  requestId += 1;
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <Teleport to="body">
    <div class="periods-backdrop" @click.self="emit('close')">
      <section
        class="periods-dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
      >
        <button
          ref="closeButton"
          type="button"
          class="periods-close"
          title="Закрыть"
          aria-label="Закрыть"
          @click="emit('close')"
        >
          <svg
            class="periods-close-icon"
            viewBox="0 0 12 12"
            aria-hidden="true"
          >
            <path d="M2 2L10 10M10 2L2 10" />
          </svg>
        </button>

        <h2 :id="titleId" class="periods-title">Периоды</h2>
        <p class="periods-subtitle">{{ video.title }}</p>

        <div v-if="loading" class="periods-status">Загрузка…</div>
        <div v-else-if="error" class="periods-status is-error">
          {{ error }}
        </div>
        <div v-else-if="!hasPeriods" class="periods-status">
          {{ emptyMessage }}
        </div>
        <div v-else class="periods-sections">
          <section v-if="mainRows.length" class="periods-section">
            <h3 class="periods-section-title">Основная тема</h3>
            <PeriodsTable :rows="mainRows" />
          </section>

          <section
            v-if="showIndirectVideos && indirectRows.length"
            class="periods-section"
          >
            <h3 class="periods-section-title">Упомянуто косвенно</h3>
            <PeriodsTable :rows="indirectRows" />
          </section>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.periods-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.64);
  overscroll-behavior: contain;
}

.periods-dialog {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-sizing: border-box;
  width: min(560px, 100%);
  max-height: calc(100vh - 48px);
  padding: 22px;
  color: #f4f0e6;
  background: #300000;
  border: 1px solid rgba(255, 216, 102, 0.36);
  border-radius: 12px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
}

.periods-dialog > * {
  flex: 0 0 auto;
}

.periods-close {
  position: absolute;
  top: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.periods-close:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.periods-close-icon {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
}

.periods-title {
  margin: 0;
  padding-right: 36px;
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

.periods-subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.62);
  overflow-wrap: anywhere;
}

.periods-status {
  padding-top: 12px;
  font-size: 14px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.75);
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.periods-status.is-error {
  color: #ffb4a8;
}

.periods-sections {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 2px;
  overflow-y: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.periods-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 12px;
}

.periods-section + .periods-section {
  margin-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.periods-section-title {
  margin: 0;
  padding: 0 10px 6px;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

@media (max-width: 520px) {
  .periods-backdrop {
    padding: 12px;
  }

  .periods-dialog {
    max-height: calc(100vh - 24px);
    padding: 16px;
  }

  .periods-title {
    font-size: 19px;
  }

  .periods-section-title {
    font-size: 15px;
  }
}

@media (max-width: 720px) {
  .periods-backdrop {
    z-index: 80;
    padding: 8px;
  }

  .periods-dialog {
    width: 100%;
    max-height: calc(100dvh - 16px);
  }
}
</style>
