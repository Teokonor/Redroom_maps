import { nextTick, onBeforeUnmount, onMounted, ref, type Ref } from 'vue';
import * as d3 from 'd3';
import { MAP_RENDER_REFRESH_MS } from '@/config/map';

export function useMapZoom(
  svgRef: Ref<SVGSVGElement | null>,
  mapGroupRef: Ref<SVGGElement | null>
) {
  const zoomScale = ref(1);
  const mapRenderKey = ref(0);

  let zoomBehavior: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null;
  let currentZoomTransform = d3.zoomIdentity;
  let mapRefreshTimer: number | null = null;

  // Полный перерендер карты без смены года, масштаба, выбранной страны
  // и текущего зума. Нужен как страховка от «фантомных» SVG-узлов,
  // которые иногда остаются после частых переключений карт.
  async function refreshMapRender() {
    mapRenderKey.value += 1;
    await nextTick();

    if (mapGroupRef.value) {
      d3.select(mapGroupRef.value).attr(
        'transform',
        currentZoomTransform.toString()
      );
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      void refreshMapRender();
    }
  }

  function resetZoom() {
    if (!svgRef.value || !zoomBehavior) return;

    d3.select(svgRef.value).call(
      zoomBehavior.transform,
      d3.zoomIdentity
    );
  }

  onMounted(() => {
    zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([1, 10000])
      .filter((event: MouseEvent) => {
        if (event.type === 'mousedown') {
          if (event.button === 1) return true;
          return event.button === 0 && !event.ctrlKey;
        }

        return (!event.ctrlKey || event.type === 'wheel') && !event.button;
      })
      .on('zoom', (event) => {
        zoomScale.value = event.transform.k;
        currentZoomTransform = event.transform;
        d3.select(mapGroupRef.value).attr('transform', event.transform);
      });

    if (svgRef.value) {
      d3.select(svgRef.value).call(zoomBehavior);
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);

    mapRefreshTimer = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return;
      void refreshMapRender();
    }, MAP_RENDER_REFRESH_MS);
  });

  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);

    if (mapRefreshTimer !== null) {
      window.clearInterval(mapRefreshTimer);
      mapRefreshTimer = null;
    }
  });

  return {
    zoomScale,
    mapRenderKey,
    resetZoom,
  };
}
