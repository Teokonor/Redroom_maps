<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import type { Tag } from '@/types/tag';
import type { Video } from '@/types/video';
import { loadTags } from '@/api/tags';
import { loadTagVideos } from '@/api/videos';
import VideoCard from '@/components/VideoCard.vue';
import VideoDetails from '@/components/VideoDetails.vue';
import { useVideoCatalog } from '@/composables/useVideoCatalog';

type Panel = 'collections' | 'help' | 'support';

const props = defineProps<{
  panel: Panel;
}>();

const emit = defineEmits<{
  close: [];
}>();

const panelTitle = computed(() => {
  const titles: Record<Panel, string> = {
    collections: 'Подборки',
    help: 'Справка',
    support: 'Поддержать',
  };
  return titles[props.panel];
});

const tags = ref<Tag[]>([]);
const selectedTagId = ref<string | null>(null);
const videos = ref<Video[]>([]);
const tagsLoading = ref(false);
const videosLoading = ref(false);
const tagsError = ref<string | null>(null);
const videosError = ref<string | null>(null);
const selectedVideo = ref<Video | null>(null);

const { ensureCatalog } = useVideoCatalog();

let tagsRequestId = 0;
let videosRequestId = 0;

const sortedTags = computed(() =>
  [...tags.value].sort((a, b) => a.name.localeCompare(b.name, 'ru'))
);

const selectedTag = computed(
  () => tags.value.find((tag) => tag.id === selectedTagId.value) ?? null
);

const collectionTitle = computed(
  () => selectedTag.value?.name ?? 'Все видео'
);

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

async function loadTagsOnce() {
  if (tags.value.length > 0 || tagsLoading.value) return;

  const requestId = ++tagsRequestId;
  tagsLoading.value = true;
  tagsError.value = null;

  try {
    const nextTags = await loadTags();
    if (requestId !== tagsRequestId) return;
    tags.value = nextTags;
  } catch (error) {
    if (requestId !== tagsRequestId) return;
    tagsError.value = errorMessage(error, 'Не удалось загрузить теги');
  } finally {
    if (requestId === tagsRequestId) tagsLoading.value = false;
  }
}

async function loadVideos(tagId: string | null) {
  const requestId = ++videosRequestId;
  videosLoading.value = true;
  videosError.value = null;
  videos.value = [];

  try {
    const nextVideos = tagId
      ? await loadTagVideos(tagId)
      : await ensureCatalog();

    if (requestId !== videosRequestId) return;
    videos.value = [...nextVideos].sort((a, b) => b.num - a.num);
  } catch (error) {
    if (requestId !== videosRequestId) return;
    videosError.value = errorMessage(error, 'Не удалось загрузить видео');
  } finally {
    if (requestId === videosRequestId) videosLoading.value = false;
  }
}

function selectTag(tagId: string | null) {
  if (selectedTagId.value === tagId && !videosError.value) {
    return;
  }

  selectedTagId.value = tagId;
  void loadVideos(tagId);
}

function ensureCollections() {
  void loadTagsOnce();

  if (
    videos.value.length === 0 &&
    !videosLoading.value &&
    !videosError.value
  ) {
    void loadVideos(selectedTagId.value);
  }
}

watch(
  () => props.panel,
  (panel) => {
    selectedVideo.value = null;

    if (panel === 'collections') {
      ensureCollections();
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  tagsRequestId += 1;
  videosRequestId += 1;
});
</script>

<template>
  <aside class="top-panel" role="dialog" :aria-label="panelTitle">
    <div class="top-panel-header">
      <h2 class="top-panel-title">{{ panelTitle }}</h2>
      <button
        type="button"
        class="top-panel-close"
        title="Закрыть"
        aria-label="Закрыть"
        @click="emit('close')"
      >
        <svg
          class="top-panel-close-icon"
          viewBox="0 0 12 12"
          aria-hidden="true"
        >
          <path d="M2 2L10 10M10 2L2 10" />
        </svg>
      </button>
    </div>

    <div v-if="panel === 'collections'" class="top-panel-body collections">
      <aside class="tag-list" aria-label="Теги">
        <div v-if="tagsLoading" class="top-panel-status">
          Загрузка…
        </div>
        <div v-else-if="tagsError" class="top-panel-status is-error">
          {{ tagsError }}
        </div>

        <button
          type="button"
          class="tag-button"
          :class="{ 'is-active': selectedTagId === null }"
          @click="selectTag(null)"
        >
          Все видео
        </button>

        <button
          v-for="tag in sortedTags"
          :key="tag.id"
          type="button"
          class="tag-button"
          :class="{ 'is-active': selectedTagId === tag.id }"
          @click="selectTag(tag.id)"
        >
          <span class="tag-name">{{ tag.name }}</span>
          <span class="tag-count">{{ tag.video_count }}</span>
        </button>
      </aside>

      <section class="collection-videos" :aria-label="collectionTitle">
        <h3 class="collection-title">{{ collectionTitle }}</h3>

        <div v-if="videosLoading" class="top-panel-status">
          Загрузка…
        </div>
        <div v-else-if="videosError" class="top-panel-status is-error">
          {{ videosError }}
        </div>
        <ul v-else-if="videos.length" class="top-panel-video-list">
          <VideoCard
            v-for="video in videos"
            :key="video.num"
            :video="video"
            @open="selectedVideo = $event"
          />
        </ul>
        <div v-else class="top-panel-status">
          Нет видео
        </div>
      </section>
    </div>

    <div v-else class="top-panel-body top-panel-placeholder">
      <p v-if="panel === 'help'">
        Здесь будет справка по проекту.
      </p>
      <p v-else>
        Здесь будет информация о поддержке проекта.
      </p>
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
.top-panel {
  position: fixed;
  top: 60px;
  right: 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: clamp(600px, 36vw, 740px);
  max-width: 100vw;
  height: calc(100vh - 60px);
  padding: 18px;
  overflow: hidden;
  color: #f4f0e6;
  background: #300000;
  border-left: 1px solid rgba(255, 216, 102, 0.36);
  box-shadow: -16px 0 34px rgba(0, 0, 0, 0.42);
}

.top-panel-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.top-panel-title {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  line-height: 1.2;
  color: #f4f0e6;
}

.top-panel-close {
  display: inline-flex;
  flex: 0 0 auto;
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

.top-panel-close:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.top-panel-close-icon {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
}

.top-panel-body {
  flex: 1;
  min-height: 0;
}

.collections {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr);
  gap: 16px;
}

.tag-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
  overflow-y: auto;
}

.tag-button {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  font: inherit;
  font-size: 13px;
  line-height: 1.35;
  color: #f4f0e6;
  text-align: left;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition:
    background 0.15s,
    border-color 0.15s;
}

.tag-button:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.tag-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.tag-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-count {
  flex: 0 0 auto;
  font-size: 11px;
  opacity: 0.75;
}

.collection-videos {
  min-width: 0;
  min-height: 0;
  padding-right: 12px;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.collection-title {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

.top-panel-video-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.top-panel-status {
  font-size: 14px;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.75);
}

.top-panel-status.is-error {
  color: #ffb4a8;
}

.top-panel-placeholder {
  padding-top: 12px;
  font-size: 16px;
  line-height: 1.6;
  color: rgba(244, 240, 230, 0.82);
}

.top-panel-placeholder p {
  margin: 0;
}

@media (max-width: 700px) {
  .top-panel {
    width: 100%;
  }

  .collections {
    grid-template-columns: 120px minmax(0, 1fr);
  }
}
</style>
