import { computed, shallowRef } from 'vue';
import type { Video } from '@/types/video';
import { loadAllVideos } from '@/api/videos';

const catalog = shallowRef<Video[]>([]);
let catalogPromise: Promise<Video[]> | null = null;
let catalogLoaded = false;

export function useVideoCatalog() {
  const videosByNum = computed(
    () => new Map(catalog.value.map((video) => [video.num, video]))
  );

  function ensureCatalog(): Promise<Video[]> {
    if (catalogLoaded) {
      return Promise.resolve(catalog.value);
    }

    if (!catalogPromise) {
      catalogPromise = loadAllVideos()
        .then((videos) => {
          catalog.value = videos;
          catalogLoaded = true;
          return videos;
        })
        .catch((error: unknown) => {
          catalogPromise = null;
          throw error;
        });
    }

    return catalogPromise;
  }

  return { catalog, videosByNum, ensureCatalog };
}
