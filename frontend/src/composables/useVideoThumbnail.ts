import { computed, ref, toValue, watch } from 'vue';
import type { MaybeRefOrGetter } from 'vue';
import type { Video } from '@/types/video';
import { getVideoPreviewUrl } from '@/api/videos';
import { getYouTubeThumbnailUrl } from '@/utils/youtube';

export function useVideoThumbnail(source: MaybeRefOrGetter<Video>) {
  const video = computed(() => toValue(source));

  const localThumbnail = computed(() => {
    const imageFile = video.value.image_file?.trim();
    return imageFile ? getVideoPreviewUrl(imageFile) : null;
  });

  const youtubeThumbnail = computed(
    () =>
      getYouTubeThumbnailUrl(video.value.url) ??
      getYouTubeThumbnailUrl(video.value.reserve_url)
  );

  const useYoutubeFallback = ref(false);
  const thumbnailFailed = ref(false);

  const thumbnailUrl = computed(() => {
    if (localThumbnail.value && !useYoutubeFallback.value) {
      return localThumbnail.value;
    }
    return youtubeThumbnail.value;
  });

  watch(
    () => [
      video.value.image_file,
      video.value.url,
      video.value.reserve_url,
    ],
    () => {
      useYoutubeFallback.value = false;
      thumbnailFailed.value = false;
    }
  );

  function handleThumbnailError() {
    if (
      localThumbnail.value &&
      !useYoutubeFallback.value &&
      youtubeThumbnail.value
    ) {
      useYoutubeFallback.value = true;
      return;
    }

    thumbnailFailed.value = true;
  }

  return {
    thumbnailUrl,
    thumbnailFailed,
    handleThumbnailError,
  };
}
