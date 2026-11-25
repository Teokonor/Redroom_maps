import { ref } from 'vue';

const MOBILE_MAX_WIDTH = 720;
const MOBILE_QUERY = `(max-width: ${MOBILE_MAX_WIDTH}px)`;

const mediaQuery =
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia(MOBILE_QUERY)
    : null;

const isMobile = ref(mediaQuery?.matches ?? false);

if (mediaQuery) {
  mediaQuery.addEventListener('change', (event) => {
    isMobile.value = event.matches;
  });
}

export function useMobileLayout() {
  return isMobile;
}
