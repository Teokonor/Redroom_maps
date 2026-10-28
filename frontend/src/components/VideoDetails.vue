<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import type { Video } from '@/types/video';
import { useVideoThumbnail } from '@/composables/useVideoThumbnail';
import { formatPublishedDate } from '@/utils/date';

const props = defineProps<{
  video: Video;
}>();

const emit = defineEmits<{
  close: [];
}>();

const closeButton = ref<HTMLButtonElement | null>(null);

const link = computed(
  () => props.video.url?.trim() || props.video.reserve_url?.trim() || null
);

const publishedLabel = computed(() =>
  formatPublishedDate(props.video.published)
);

const description = computed(() => props.video.description?.trim() || null);

const titleId = computed(() => `video-details-title-${props.video.num}`);

const { thumbnailUrl, thumbnailFailed, handleThumbnailError } =
  useVideoThumbnail(() => props.video);

let previousBodyOverflow = '';

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.stopPropagation();
    emit('close');
  }
}

onMounted(() => {
  previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  window.addEventListener('keydown', handleKeydown);
  closeButton.value?.focus();
});

onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow;
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <Teleport to="body">
    <div class="video-details-backdrop" @click.self="emit('close')">
      <section
        class="video-details"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
      >
        <button
          ref="closeButton"
          type="button"
          class="video-details-close"
          title="Закрыть"
          aria-label="Закрыть"
          @click="emit('close')"
        >
          <svg
            class="video-details-close-icon"
            viewBox="0 0 12 12"
            aria-hidden="true"
          >
            <path d="M2 2L10 10M10 2L2 10" />
          </svg>
        </button>

        <h2 :id="titleId" class="video-details-title">
          {{ video.title }}
        </h2>

        <div class="video-details-preview" aria-hidden="true">
          <img
            v-if="thumbnailUrl && !thumbnailFailed"
            :src="thumbnailUrl"
            alt=""
            decoding="async"
            referrerpolicy="no-referrer"
            @error="handleThumbnailError"
          />
        </div>

        <div class="video-details-meta">
          <a
            v-if="link"
            class="video-details-link"
            :href="link"
            :title="link"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ link }}
          </a>
          <time
            v-if="publishedLabel"
            class="video-details-date"
            :datetime="video.published"
          >
            Опубликовано {{ publishedLabel }}
          </time>
        </div>

        <p v-if="description" class="video-details-description">
          {{ description }}
        </p>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.video-details-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.64);
  overscroll-behavior: contain;
}

.video-details {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-sizing: border-box;
  width: min(560px, 100%);
  max-height: calc(100vh - 48px);
  padding: 22px;
  overflow-y: auto;
  color: #f4f0e6;
  background: #300000;
  border: 1px solid rgba(255, 216, 102, 0.36);
  border-radius: 12px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
}

.video-details-close {
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

.video-details-close:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.video-details-close-icon {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
}

.video-details-title {
  margin: 0;
  padding-right: 36px;
  font-size: 22px;
  font-weight: 600;
  line-height: 1.3;
  overflow-wrap: anywhere;
}

.video-details-preview {
  align-self: center;
  box-sizing: content-box;
  width: 320px;
  max-width: calc(100% - 2px);
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #707070;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
}

.video-details-preview img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-details-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.video-details-link {
  font-size: 13px;
  line-height: 1.4;
  color: #ffd866;
  text-decoration: none;
  overflow-wrap: anywhere;
}

.video-details-link:hover {
  text-decoration: underline;
}

.video-details-date {
  font-size: 13px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.62);
}

.video-details-description {
  margin: 0;
  padding-top: 12px;
  font-size: 14px;
  line-height: 1.5;
  color: rgba(244, 240, 230, 0.86);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

@media (max-width: 520px) {
  .video-details-backdrop {
    padding: 12px;
  }

  .video-details {
    max-height: calc(100vh - 24px);
    padding: 16px;
  }

  .video-details-title {
    font-size: 19px;
  }
}
</style>
