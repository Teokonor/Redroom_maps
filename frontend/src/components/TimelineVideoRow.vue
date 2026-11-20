<script setup lang="ts">
import { computed } from 'vue';
import type { Video } from '@/types/video';
import { getVideoQuality } from '@/utils/videoQuality';

const props = defineProps<{
  video: Video;
}>();

const emit = defineEmits<{
  open: [video: Video];
}>();

const link = computed(
  () => props.video.url?.trim() || props.video.reserve_url?.trim() || null
);

const quality = computed(() => getVideoQuality(props.video.quality));

function open() {
  emit('open', props.video);
}
</script>

<template>
  <div
    class="timeline-row"
    role="button"
    tabindex="0"
    :aria-label="`Подробнее о видео: ${video.title}`"
    @click="open"
    @keydown.enter.prevent="open"
    @keydown.space.prevent="open"
  >
    <span class="timeline-row-title" :title="video.title">
      {{ video.title }}
    </span>

    <span
      class="timeline-row-quality"
      role="img"
      :style="{ backgroundColor: quality.color }"
      :aria-label="quality.label"
      :title="quality.label"
      @click.stop
    />

    <a
      v-if="link"
      class="timeline-row-link"
      :href="link"
      :title="link"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Открыть на YouTube"
      @click.stop
      @keydown.stop
    >
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4 12 12 4M12 4H6M12 4v6" />
      </svg>
    </a>
  </div>
</template>

<style scoped>
.timeline-row {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  height: var(--tl-row, 34px);
  padding: 0;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.timeline-row:first-child {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.timeline-row:hover {
  background: rgba(255, 255, 255, 0.06);
}

.timeline-row:focus-visible {
  outline: 2px solid #ffd866;
  outline-offset: -2px;
}

.timeline-row-title {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.35;
  color: rgba(244, 240, 230, 0.92);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-row-quality {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  box-sizing: border-box;
}

.timeline-row-link {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  color: #ffd866;
  text-decoration: none;
  background: rgba(255, 216, 102, 0.08);
  border: 1px solid rgba(255, 216, 102, 0.32);
  border-radius: 4px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.timeline-row-link:hover {
  background: rgba(255, 216, 102, 0.2);
  border-color: rgba(255, 216, 102, 0.6);
}

.timeline-row-link svg {
  display: block;
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
