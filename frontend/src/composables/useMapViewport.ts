import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  type Ref,
} from 'vue';
import { useMobileLayout } from '@/composables/useMobileLayout';

const RULER_MARGIN = 8;

export function useMapViewport(
  mapLayoutRef: Ref<HTMLElement | null>,
  rulerWrapRef: Ref<HTMLElement | null>
) {
  const isMobile = useMobileLayout();

  const rulerCenter = ref<{ x: number; y: number } | null>(null);
  const rulerSize = ref({ width: 0, height: 0 });
  const rulerDragging = ref(false);
  const suppressRulerClick = ref(false);

  let rulerDragStart: {
    pointerX: number;
    pointerY: number;
    centerX: number;
    centerY: number;
  } | null = null;

  let rulerResizeObserver: ResizeObserver | null = null;
  let clampFrame = 0;

  const rulerStyle = computed(() => {
    if (isMobile.value || !rulerCenter.value) return {};

    const { width, height } = rulerSize.value;
    return {
      left: `${rulerCenter.value.x - width / 2}px`,
      top: `${rulerCenter.value.y - height / 2}px`,
      transform: 'none',
    };
  });

  function clampAxis(value: number, min: number, max: number): number {
    if (max < min) return (min + max) / 2;
    return Math.min(max, Math.max(min, value));
  }

  function clampRulerCenter() {
    const layout = mapLayoutRef.value;
    const wrap = rulerWrapRef.value;
    if (!layout || !wrap) return;

    const layoutWidth = layout.clientWidth;
    const layoutHeight = layout.clientHeight;
    const width = wrap.offsetWidth;
    const height = wrap.offsetHeight;
    if (!layoutWidth || !layoutHeight || !width || !height) return;

    rulerSize.value = { width, height };

    if (!rulerCenter.value) {
      rulerCenter.value = {
        x: 16 + width / 2,
        y: layoutHeight / 2,
      };
    }

    const minX = width / 2 + RULER_MARGIN;
    const maxX = layoutWidth - width / 2 - RULER_MARGIN;
    const minY = height / 2 + RULER_MARGIN;
    const maxY = layoutHeight - height / 2 - RULER_MARGIN;

    rulerCenter.value = {
      x: clampAxis(rulerCenter.value.x, minX, maxX),
      y: clampAxis(rulerCenter.value.y, minY, maxY),
    };
  }

  function isRulerDragTarget(target: EventTarget | null): boolean {
    if (!(target instanceof Element)) return false;
    if (!target.closest('.year-ruler-wrap')) return false;

    return !target.closest(
      '.ruler-collapse, .ruler-close, .year-input-row, .ticks, .zoom-controls, .pan-button, .loading'
    );
  }

  function startRulerDrag(event: PointerEvent) {
    if (isMobile.value || event.button !== 0) return;
    if (!isRulerDragTarget(event.target)) return;

    if (!rulerCenter.value) clampRulerCenter();
    if (!rulerCenter.value) return;

    suppressRulerClick.value = false;
    rulerDragging.value = true;
    rulerDragStart = {
      pointerX: event.clientX,
      pointerY: event.clientY,
      centerX: rulerCenter.value.x,
      centerY: rulerCenter.value.y,
    };

    window.addEventListener('pointermove', moveRuler, { passive: false });
    window.addEventListener('pointerup', endRulerDrag);
    window.addEventListener('pointercancel', endRulerDrag);
  }

  function moveRuler(event: PointerEvent) {
    if (!rulerDragStart) return;

    const dx = event.clientX - rulerDragStart.pointerX;
    const dy = event.clientY - rulerDragStart.pointerY;

    if (!suppressRulerClick.value && Math.hypot(dx, dy) < 3) {
      return;
    }

    suppressRulerClick.value = true;
    rulerCenter.value = {
      x: rulerDragStart.centerX + dx,
      y: rulerDragStart.centerY + dy,
    };
    clampRulerCenter();
    event.preventDefault();
  }

  function endRulerDrag() {
    rulerDragging.value = false;
    rulerDragStart = null;
    window.removeEventListener('pointermove', moveRuler);
    window.removeEventListener('pointerup', endRulerDrag);
    window.removeEventListener('pointercancel', endRulerDrag);

    // The click after a drag must be suppressed, but if the drag ended outside
    // the panel and no click fired, don't block the next real click forever.
    if (suppressRulerClick.value) {
      window.setTimeout(() => {
        suppressRulerClick.value = false;
      }, 0);
    }
  }

  function handleRulerClickCapture(event: MouseEvent) {
    if (!suppressRulerClick.value) return;

    event.preventDefault();
    event.stopPropagation();
    suppressRulerClick.value = false;
  }

  onMounted(() => {
    rulerResizeObserver = new ResizeObserver(() => {
      clampRulerCenter();
    });
    if (mapLayoutRef.value) {
      rulerResizeObserver.observe(mapLayoutRef.value);
    }
    if (rulerWrapRef.value) {
      rulerResizeObserver.observe(rulerWrapRef.value);
    }
    clampFrame = requestAnimationFrame(() => clampRulerCenter());
  });

  onBeforeUnmount(() => {
    if (clampFrame) cancelAnimationFrame(clampFrame);
    rulerResizeObserver?.disconnect();
    rulerResizeObserver = null;
    endRulerDrag();
  });

  return {
    rulerDragging,
    rulerStyle,
    startRulerDrag,
    handleRulerClickCapture,
  };
}
