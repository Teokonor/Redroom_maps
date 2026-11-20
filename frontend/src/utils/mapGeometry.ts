import * as topojson from 'topojson-client';
import type {
  CountryFeatureCollection,
  LoadedMap,
  WorldFeatureCollection,
} from '@/types/map';

type TopologyLike = {
  objects?: {
    data?: unknown;
  };
};

function getTopologyData(topology: unknown): unknown | null {
  return (topology as TopologyLike | null)?.objects?.data ?? null;
}

function getCountryColorId(geometry: { properties?: unknown }): string | null {
  const properties = geometry.properties as
    | { colorId?: string | null }
    | undefined;
  return properties?.colorId ?? null;
}

function toTopology(topology: unknown) {
  return topology as Parameters<typeof topojson.feature>[0];
}

function toGeometryObject(data: unknown) {
  return data as Parameters<typeof topojson.feature>[1] &
    Parameters<typeof topojson.mesh>[1];
}

export function parseMapTopology(
  topology: unknown,
  year: number
): LoadedMap | null {
  const dataObject = getTopologyData(topology);
  if (!dataObject) return null;

  const topologyInput = toTopology(topology);
  const dataInput = toGeometryObject(dataObject);

  const map = topojson.feature(
    topologyInput,
    dataInput
  ) as unknown as CountryFeatureCollection;

  // Границы:
  // - внешние — только у цветных объектов;
  // - между двумя бесцветными — не рисуем;
  // - между бесцветным и цветным — рисуем;
  // - между цветными — только при разных colorId.
  const borders = topojson.mesh(
    topologyInput,
    dataInput,
    (a, b) => {
      const aColorId = getCountryColorId(a);
      const bColorId = getCountryColorId(b);

      if (a === b) return Boolean(aColorId);
      if (!aColorId && !bColorId) return false;
      if (!aColorId || !bColorId) return true;
      return aColorId !== bColorId;
    }
  );

  // Границы регионов: внутренние стыки объектов с одинаковым colorId.
  // По умолчанию не рисуются, включаются переключателем «Границы регионов».
  const regionBorders = topojson.mesh(
    topologyInput,
    dataInput,
    (a, b) => {
      if (a === b) return false;

      const aColorId = getCountryColorId(a);
      const bColorId = getCountryColorId(b);

      return Boolean(aColorId) && aColorId === bColorId;
    }
  );

  return { year, map, borders, regionBorders };
}

export function parseWorldTopology(
  topology: unknown
): WorldFeatureCollection | null {
  const dataObject = getTopologyData(topology);
  if (!dataObject) return null;

  return topojson.feature(
    toTopology(topology),
    toGeometryObject(dataObject)
  ) as unknown as WorldFeatureCollection;
}
