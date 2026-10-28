<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Video } from '@/types/video';
import { useVideoThumbnail } from '@/composables/useVideoThumbnail';

const props = defineProps<{
  video: Video;
}>();

const emit = defineEmits<{
  open: [video: Video];
}>();

const link = computed(
  () => props.video.url?.trim() || props.video.reserve_url?.trim() || null
);

const { thumbnailUrl, thumbnailFailed, handleThumbnailError } =
  useVideoThumbnail(() => props.video);

const qualityTooltipVisible = ref(false);

function openDetails() {
  emit('open', props.video);
}

const quality = computed(() => {
  const raw = props.video.quality?.trim() ?? '';
  const normalized = raw.startsWith('#') ? raw.slice(1) : raw;

  if (!/^[0-9a-f]{6}$/i.test(normalized)) {
    return {
      color: '#808080',
      label: 'Качество видео: неизвестно',
    };
  }

  const MAX_CHANNEL = 153;
  const red = parseInt(normalized.slice(0, 2), 16);
  const green = parseInt(normalized.slice(2, 4), 16);
  const redValue = Math.min(MAX_CHANNEL, Math.max(0, red));
  const greenValue = Math.min(MAX_CHANNEL, Math.max(0, green));

  // Градиент двухфазный: красный -> жёлтый (растёт зелёный),
  // затем жёлтый -> зелёный (убывает красный).
  const score =
    greenValue < MAX_CHANNEL
      ? (greenValue / MAX_CHANNEL) * 0.5
      : 0.5 + ((MAX_CHANNEL - redValue) / MAX_CHANNEL) * 0.5;

  let level: 'низкое' | 'среднее' | 'высокое' | 'высшее';
  if (score < 1 / 3) {
    level = 'низкое';
  } else if (score < 2 / 3) {
    level = 'среднее';
  } else if (score < 1) {
    level = 'высокое';
  } else {
    level = 'высшее';
  }

  return {
    color: `#${normalized.toLowerCase()}`,
    label: `Качество видео: ${level}`,
  };
});
</script>

<template>
  <li
    class="video-card"
    role="button"
    tabindex="0"
    aria-haspopup="dialog"
    :aria-label="`Подробнее о видео: ${video.title}`"
    @click="openDetails"
    @keydown.enter.prevent="openDetails"
    @keydown.space.prevent="openDetails"
  >
    <div class="video-card-preview" aria-hidden="true">
      <img
        v-if="thumbnailUrl && !thumbnailFailed"
        :src="thumbnailUrl"
        alt=""
        loading="lazy"
        decoding="async"
        referrerpolicy="no-referrer"
        @error="handleThumbnailError"
      />
    </div>

    <div class="video-card-text">
      <div class="video-card-title" :title="video.title">
        {{ video.title }}
      </div>

      <div class="video-card-meta">
        <a
          v-if="link"
          class="video-card-link"
          :href="link"
          :title="link"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
          @keydown.stop
        >
          {{ link }}
        </a>
        <span
          v-else
          class="video-card-link is-empty"
          aria-hidden="true"
        />

        <span
          class="video-quality"
          role="img"
          :style="{ backgroundColor: quality.color }"
          :aria-label="quality.label"
          @click.stop
          @mouseenter="qualityTooltipVisible = true"
          @mouseleave="qualityTooltipVisible = false"
        >
          <span
            v-if="qualityTooltipVisible"
            class="video-quality-tooltip"
          >
            {{ quality.label }}
          </span>
        </span>
      </div>
    </div>
  </li>
</template>

<style scoped>
.video-card {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  box-sizing: border-box;
  padding: 8px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.video-card:hover {
  background: rgba(255, 255, 255, 0.11);
  border-color: rgba(255, 255, 255, 0.24);
}

.video-card:focus-visible {
  outline: 2px solid #ffd866;
  outline-offset: 2px;
}

.video-card-preview {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #707070;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
}

.video-card-preview img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-card-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.video-card-title {
  overflow: hidden;
  font-size: 14px;
  line-height: 1.35;
  color: rgba(244, 240, 230, 0.95);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.video-card-link {
  display: block;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 1.35em;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.35;
  color: #ffd866;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-card-link:hover {
  text-decoration: underline;
}

.video-card-link.is-empty {
  visibility: hidden;
}

.video-quality {
  position: relative;
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  box-sizing: border-box;
}

.video-quality-tooltip {
  position: absolute;
  right: -2px;
  bottom: calc(100% + 6px);
  z-index: 5;
  padding: 5px 8px;
  font-size: 11px;
  line-height: 1.3;
  color: #f4f0e6;
  white-space: nowrap;
  pointer-events: none;
  background: #000035;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
}
</style>
