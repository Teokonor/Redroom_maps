<script setup lang="ts">
import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
} from 'vue';
import type { Video } from '@/types/video';
import TimelineVideoRow from '@/components/TimelineVideoRow.vue';
import { formatYearHuman } from '@/utils/yearLabels';
import {
  TIMELINE_BOTTOM_LABEL_HEIGHT,
  TIMELINE_GAP_HEIGHT,
  TIMELINE_LABEL_HEIGHT,
  TIMELINE_ROW_HEIGHT,
  timelineContentHeight,
  type TimelineBlock,
} from '@/utils/videoTimeline';

const props = defineProps<{
  idPrefix: string;
  title: string;
  blocks: TimelineBlock[];
  anchorIndex: number;
  videosByNum: Map<number, Video>;
}>();

const emit = defineEmits<{
  open: [video: Video];
}>();

const showFuture = ref(false);
const visibleKeys = reactive(new Set<string>());
const elements = new Map<string, Element>();
let observer: IntersectionObserver | null = null;

const hasFuture = computed(() =>
  props.blocks
    .slice(props.anchorIndex + 1)
    .some((block) => !block.isGap && block.videoNums.length > 0)
);

const displayBlocks = computed(() => {
  const visible = showFuture.value
    ? props.blocks
    : props.blocks.slice(0, props.anchorIndex + 1);
  return [...visible].reverse();
});

const cssVars = computed(() => ({
  '--tl-row': `${TIMELINE_ROW_HEIGHT}px`,
}));

function videosFor(block: TimelineBlock): Video[] {
  const videos: Video[] = [];
  for (const videoNum of block.videoNums) {
    const video = props.videosByNum.get(videoNum);
    if (video) videos.push(video);
  }
  return videos.sort((left, right) => right.num - left.num);
}

function renderRows(block: TimelineBlock, index: number): boolean {
  if (block.isGap) return false;
  if (index < 2) return true;
  if (props.blocks[props.anchorIndex]?.key === block.key) return true;
  return visibleKeys.has(block.key);
}

function topLabel(block: TimelineBlock, index: number): string {
  const year = formatYearHuman(block.endYear);

  if (block.singleYear) return `${year} начало`;

  const above = displayBlocks.value[index - 1];
  if (above?.singleYear && above.endYear === block.endYear) {
    return `${year} конец`;
  }

  return year;
}

function bottomLabel(block: TimelineBlock): string {
  const year = formatYearHuman(block.beginYear);
  return block.singleYear ? `${year} конец` : year;
}

function setBlockElement(key: string, element: unknown) {
  const next = element instanceof Element ? element : null;
  const previous = elements.get(key);

  if (previous && previous !== next) observer?.unobserve(previous);

  if (next) {
    elements.set(key, next);
    observer?.observe(next);
  } else {
    elements.delete(key);
  }
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const element = entry.target as HTMLElement;
        const key = element.dataset.blockKey;
        if (!key) continue;

        if (entry.isIntersecting) {
          visibleKeys.add(key);
        } else {
          visibleKeys.delete(key);
        }
      }
    },
    { rootMargin: '600px 0px' }
  );

  for (const element of elements.values()) {
    observer.observe(element);
  }
});

onBeforeUnmount(() => {
  observer?.disconnect();
  observer = null;
  elements.clear();
  visibleKeys.clear();
});
</script>

<template>
  <section class="history-timeline-section">
    <div class="history-timeline-head">
      <h3 class="history-timeline-title">{{ title }}</h3>

      <button
        v-if="hasFuture && !showFuture"
        type="button"
        class="history-future-button"
        @click="showFuture = true"
      >
        ^ Смотреть будущее
      </button>
    </div>

    <div
      v-if="displayBlocks.length"
      class="history-timeline"
      :style="cssVars"
    >
      <div
        v-for="(block, index) in displayBlocks"
        :key="block.key"
        class="timeline-block"
        :data-timeline-block="`${idPrefix}:${block.key}`"
      >
        <div
          class="timeline-label"
          :style="{ height: `${TIMELINE_LABEL_HEIGHT}px` }"
        >
          <span class="timeline-tick" aria-hidden="true" />
          <span class="timeline-year">{{ topLabel(block, index) }}</span>
        </div>

        <div
          :ref="(element) => setBlockElement(block.key, element)"
          class="timeline-body"
          :data-block-key="block.key"
          :style="{ height: `${timelineContentHeight(block)}px` }"
        >
          <div
            v-if="block.isGap"
            class="timeline-gap"
            :style="{ height: `${TIMELINE_GAP_HEIGHT}px` }"
            aria-hidden="true"
          />
          <template v-else-if="renderRows(block, index)">
            <TimelineVideoRow
              v-for="video in videosFor(block)"
              :key="video.num"
              :video="video"
              @open="emit('open', $event)"
            />
          </template>
        </div>

        <div
          v-if="index === displayBlocks.length - 1"
          class="timeline-label timeline-label-bottom"
          :style="{ height: `${TIMELINE_BOTTOM_LABEL_HEIGHT}px` }"
        >
          <span class="timeline-tick" aria-hidden="true" />
          <span class="timeline-year">{{ bottomLabel(block) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="history-timeline-empty">Нет видео</div>
  </section>
</template>

<style scoped>
.history-timeline-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-timeline-section + .history-timeline-section {
  margin-top: 24px;
}

.history-timeline-head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.history-timeline-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

.history-future-button {
  width: auto;
  padding: 5px 9px;
  font: inherit;
  font-size: 12px;
  line-height: 1.2;
  color: #ffd866;
  cursor: pointer;
  background: rgba(255, 216, 102, 0.08);
  border: 1px solid rgba(255, 216, 102, 0.4);
  border-radius: 5px;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s;
}

.history-future-button:hover {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.history-future-button:focus-visible {
  outline: 2px solid #ffd866;
  outline-offset: 2px;
}

.history-timeline {
  position: relative;
  box-sizing: border-box;
}

.history-timeline::before {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  content: '';
  background: #ffd866;
  opacity: 0.75;
}

.timeline-block {
  display: flex;
  flex-direction: column;
}

.timeline-label {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
}

.timeline-tick {
  flex: 0 0 auto;
  width: clamp(90px, 45%, 240px);
  height: 2px;
  background: #ffd866;
  border-radius: 1px;
}

.timeline-year {
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.2;
  color: #ffd866;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.timeline-body {
  box-sizing: border-box;
  padding-left: 10px;
}

.timeline-gap {
  box-sizing: border-box;
}

.timeline-label-bottom .timeline-year {
  color: rgba(255, 216, 102, 0.82);
}

.history-timeline-empty {
  font-size: 14px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.75);
}

@media (max-width: 1100px) {
  .timeline-tick {
    width: clamp(80px, 42%, 200px);
  }

  .timeline-year {
    font-size: 11px;
  }

  .timeline-body {
    padding-left: 8px;
  }
}

@media (max-width: 720px) {
  .timeline-tick {
    width: 30%;
  }

  .timeline-year {
    font-size: 10px;
  }
}
</style>
