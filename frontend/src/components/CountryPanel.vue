<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import type { Country, CountryRegion } from '@/types/country';
import type {
  HistoryVideoSelection,
  Video,
  VideoPeriodGroup,
  VideoSelection,
} from '@/types/video';
import {
  loadCountryHistoryVideos,
  loadCountryVideos,
} from '@/api/videos';
import HistoryTimeline from '@/components/HistoryTimeline.vue';
import VideoCard from '@/components/VideoCard.vue';
import VideoDetails from '@/components/VideoDetails.vue';
import { formatYearPeriod, getYearQueryRange } from '@/utils/yearLabels';
import {
  buildTimelineBlocks,
  findAnchorIndex,
} from '@/utils/videoTimeline';

const props = defineProps<{
  country: Country | null;
  countryId: string;
  year: number;
  fallbackName?: string | null;
  parentId: string | null;
  parentName: string | null;
  regions: CountryRegion[];
}>();

const emit = defineEmits<{
  close: [];
  'select-country': [countryId: string];
}>();

const title = computed(
  () => props.country?.name || props.fallbackName || props.countryId
);

const yearPeriod = computed(() => formatYearPeriod(props.year));
const queryRange = computed(() => getYearQueryRange(props.year));

const isRegionsTab = ref(false);
const sortedRegions = computed(() =>
  [...props.regions].sort((a, b) => a.name.localeCompare(b.name, 'ru'))
);

type VideosMode = 'period' | 'history';
type HistoryView = 'release' | 'chronology';

const mode = ref<VideosMode>('period');
const selection = ref<VideoSelection>({ main: [], indirectly: [] });
const historyPeriods = ref<VideoPeriodGroup[]>([]);
const historyView = ref<HistoryView>('release');
const panelBodyRef = ref<HTMLElement | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const selectedVideo = ref<Video | null>(null);

let requestId = 0;

const videosByNum = computed(() => {
  const index = new Map<number, Video>();
  for (const video of [
    ...selection.value.main,
    ...selection.value.indirectly,
  ]) {
    index.set(video.num, video);
  }
  return index;
});

const timelinePeriods = computed<VideoPeriodGroup[]>(() =>
  historyPeriods.value
    .map((period) => ({
      ...period,
      video_nums: period.video_nums.filter((num) =>
        videosByNum.value.has(num)
      ),
    }))
    .filter((period) => period.video_nums.length > 0)
);

const mainTimelineBlocks = computed(() =>
  buildTimelineBlocks(
    timelinePeriods.value.filter((period) => period.is_main)
  )
);

const indirectTimelineBlocks = computed(() =>
  buildTimelineBlocks(
    timelinePeriods.value.filter((period) => !period.is_main)
  )
);

const mainAnchorIndex = computed(() =>
  findAnchorIndex(mainTimelineBlocks.value, props.year)
);

const indirectAnchorIndex = computed(() =>
  findAnchorIndex(indirectTimelineBlocks.value, props.year)
);

async function loadSelection(nextMode: VideosMode) {
  const currentRequest = ++requestId;
  mode.value = nextMode;
  isLoading.value = true;
  errorMessage.value = null;
  selection.value = { main: [], indirectly: [] };
  historyPeriods.value = [];

  if (nextMode === 'period') {
    historyView.value = 'release';
  }

  try {
    const range = queryRange.value;
    let nextSelection: VideoSelection;
    let nextPeriods: VideoPeriodGroup[] = [];

    if (nextMode === 'history') {
      const historySelection: HistoryVideoSelection =
        await loadCountryHistoryVideos(props.countryId);
      nextSelection = {
        main: historySelection.main,
        indirectly: historySelection.indirectly,
      };
      nextPeriods = historySelection.periods;
    } else {
      nextSelection = await loadCountryVideos(
        props.countryId,
        range.begin,
        range.end
      );
    }

    if (currentRequest !== requestId) return;
    selection.value = nextSelection;
    historyPeriods.value = nextPeriods;
  } catch (error) {
    if (currentRequest !== requestId) return;
    errorMessage.value =
      error instanceof Error ? error.message : 'Не удалось загрузить видео';
  } finally {
    if (currentRequest === requestId) isLoading.value = false;
  }
}

function scrollToTop() {
  void nextTick(() => {
    if (panelBodyRef.value) panelBodyRef.value.scrollTop = 0;
  });
}

function showPeriodVideos() {
  if (mode.value === 'period' && !isLoading.value && !errorMessage.value) return;
  historyView.value = 'release';
  scrollToTop();
  void loadSelection('period');
}

function showHistoryVideos() {
  if (mode.value === 'history' && !isLoading.value && !errorMessage.value) return;
  historyView.value = 'release';
  scrollToTop();
  void loadSelection('history');
}

function setHistoryView(view: HistoryView) {
  if (historyView.value === view) return;
  historyView.value = view;
  scrollToTop();
}

function selectParent() {
  if (props.parentId) {
    emit('select-country', props.parentId);
  }
}

function showCountry() {
  isRegionsTab.value = false;
}

function showRegions() {
  isRegionsTab.value = true;
}

function selectRegion(regionId: string) {
  emit('select-country', regionId);
}

watch(
  () => [props.countryId, props.year] as const,
  () => {
    isRegionsTab.value = false;
    selectedVideo.value = null;
    historyView.value = 'release';
    scrollToTop();
    void loadSelection('period');
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  requestId += 1;
});
</script>

<template>
  <aside class="country-panel" @click.stop>
    <div class="country-panel-fixed">
      <div class="country-panel-header">
      <button
        type="button"
        class="country-panel-close"
        title="Закрыть"
        aria-label="Закрыть"
        @click="emit('close')"
      >
        <svg
          class="country-panel-close-icon"
          viewBox="0 0 12 12"
          aria-hidden="true"
        >
          <path d="M2 2L10 10M10 2L2 10" />
        </svg>
      </button>
    </div>

    <div class="country-tabs">
      <div class="country-tab-slot">
        <button
          v-if="parentId"
          type="button"
          class="country-tab"
          :title="parentName ?? parentId"
          @click="selectParent"
        >
          {{ parentName || parentId }}
        </button>
      </div>
      <button
        type="button"
        class="country-tab"
        :class="{ 'is-active': !isRegionsTab }"
        :title="title"
        @click="showCountry"
      >
        {{ title }}
      </button>
      <button
        type="button"
        class="country-tab"
        :class="{ 'is-active': isRegionsTab }"
        @click="showRegions"
      >
        Регионы
      </button>
    </div>

    <div
      v-if="!isRegionsTab"
      class="country-tabs country-tabs-secondary"
    >
      <button
        type="button"
        class="country-tab"
        :class="{ 'is-active': mode === 'period' }"
        @click="showPeriodVideos"
      >
        {{ yearPeriod }}
      </button>
      <button
        type="button"
        class="country-tab"
        :class="{ 'is-active': mode === 'history' }"
        @click="showHistoryVideos"
      >
        вся история
      </button>
    </div>

      <div
        v-if="mode === 'history' && !isRegionsTab"
        class="country-tabs country-tabs-secondary history-view-switch"
      >
        <button
          type="button"
          class="country-tab"
          :class="{ 'is-active': historyView === 'release' }"
          @click="setHistoryView('release')"
        >
          в порядке выхода
        </button>
        <button
          type="button"
          class="country-tab"
          :class="{ 'is-active': historyView === 'chronology' }"
          @click="setHistoryView('chronology')"
        >
          по хронологии
        </button>
      </div>

      <div
        class="country-name"
        :class="{ 'is-regions': isRegionsTab }"
      >
        {{ title }}
      </div>

    </div>

    <div ref="panelBodyRef" class="country-panel-scroll">
      <template v-if="!isRegionsTab">
        <div v-if="isLoading" class="country-videos-status">
          Загрузка…
        </div>
        <div
          v-else-if="errorMessage"
          class="country-videos-status is-error"
        >
          {{ errorMessage }}
        </div>
        <div v-else class="country-videos">
          <template
            v-if="historyView === 'release' || mode !== 'history'"
          >
            <section class="country-video-section">
              <h3 class="country-video-heading">Основная тема</h3>
              <ul v-if="selection.main.length" class="country-video-list">
                <VideoCard
                  v-for="video in selection.main"
                  :key="video.num"
                  :video="video"
                  @open="selectedVideo = $event"
                />
              </ul>
              <div v-else class="country-videos-empty">Нет видео</div>
            </section>

            <section class="country-video-section">
              <h3 class="country-video-heading">Упомянуто косвенно</h3>
              <ul
                v-if="selection.indirectly.length"
                class="country-video-list"
              >
                <VideoCard
                  v-for="video in selection.indirectly"
                  :key="video.num"
                  :video="video"
                  @open="selectedVideo = $event"
                />
              </ul>
              <div v-else class="country-videos-empty">Нет видео</div>
            </section>
          </template>

          <template v-else>
            <HistoryTimeline
              id-prefix="main"
              :key="`main-${countryId}-${year}`"
              title="Основная тема"
              :blocks="mainTimelineBlocks"
              :anchor-index="mainAnchorIndex"
              :videos-by-num="videosByNum"
              @open="selectedVideo = $event"
            />
            <HistoryTimeline
              id-prefix="indirect"
              :key="`indirect-${countryId}-${year}`"
              title="Упомянуто косвенно"
              :blocks="indirectTimelineBlocks"
              :anchor-index="indirectAnchorIndex"
              :videos-by-num="videosByNum"
              @open="selectedVideo = $event"
            />
          </template>
        </div>
      </template>

      <div v-else class="country-regions">
        <div v-if="sortedRegions.length === 0" class="country-regions-empty">
          Нет регионов
        </div>
        <button
          v-for="region in sortedRegions"
          :key="region.id"
          type="button"
          class="country-region"
          :title="region.name"
          @click="selectRegion(region.id)"
        >
          {{ region.name }}
        </button>
      </div>
    </div>

    <VideoDetails
      v-if="selectedVideo"
      :video="selectedVideo"
      @close="selectedVideo = null"
      @select="selectedVideo = $event"
    />
  </aside>
</template>

<style scoped>
.country-panel {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  width: 33.3333%;
  height: calc(100vh - 60px);
  padding: 16px 0 16px 16px;
  overflow: hidden;
  color: #f4f0e6;
  background: #300000;
  border-left: 1px solid rgba(255, 216, 102, 0.36);
  box-shadow: -16px 0 34px rgba(0, 0, 0, 0.42);
}

.country-panel-fixed {
  flex: 0 0 auto;
  padding-right: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.country-panel-scroll {
  flex: 1 1 auto;
  min-height: 0;
  padding-right: 10px;
  overflow-y: auto;
}

.country-panel-header {
  display: flex;
  flex: 0 0 auto;
  justify-content: flex-end;
  height: 24px;
  margin-bottom: 4px;
}

.country-panel-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.country-panel-close-icon {
  display: block;
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
}

.country-panel-close:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.country-tabs {
  display: grid;
  flex: 0 0 auto;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.country-tabs-secondary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 6px;
}

.history-view-switch {
  margin-top: 10px;
}

.country-tab-slot {
  min-width: 0;
}

.country-tab {
  width: 100%;
  min-width: 0;
  padding: 8px 6px;
  overflow: hidden;
  font: inherit;
  font-size: 12px;
  color: #f4f0e6;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.country-tab:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.country-tab.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.country-name {
  margin-top: 16px;
  font-size: 32px;
  font-weight: 600;
  line-height: 1.2;
  color: #f4f0e6;
  overflow-wrap: anywhere;
}

.country-name.is-regions {
  margin-top: 10px;
}

.country-regions {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  gap: 6px;
  margin-top: 16px;
}

.country-region {
  width: 100%;
  padding: 9px 12px;
  font: inherit;
  font-size: 14px;
  line-height: 1.35;
  color: #f4f0e6;
  text-align: left;
  overflow-wrap: anywhere;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.country-region:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.country-regions-empty,
.country-videos-empty {
  font-size: 14px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.75);
}

.country-videos {
  margin-top: 20px;
}

.country-video-section + .country-video-section {
  margin-top: 20px;
}

.country-video-heading {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

.country-video-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.country-videos-status {
  margin-top: 20px;
  font-size: 14px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.75);
}

.country-videos-status.is-error {
  color: #ffb4a8;
}

@media (max-width: 600px) {
  .country-panel {
    position: fixed;
    top: var(--mobile-header-height, 52px);
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 30;
    box-sizing: border-box;
    width: 100%;
    height: auto;
    padding: 12px;
    border-left: 0;
  }

  .country-name {
    margin-top: 12px;
    font-size: 24px;
  }

  .country-tab {
    padding: 7px 4px;
    font-size: 11px;
  }

  .history-view-switch {
    margin-top: 8px;
  }
}
</style>
