export type CountryProperties = {
  id: string;
  colorId: string | null;
  name: string | null;
  parent: string | null;
};

export type CountryShape = {
  id: string;
  parent: string | null;
  name: string | null;
  d: string;
  fill: string;
};

export type CountryFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Geometry,
  CountryProperties
>;

export type WorldFeatureCollection =
  GeoJSON.FeatureCollection<GeoJSON.Geometry>;

export type WorldVariant = 'modern' | 'ancient';

export type YearRangePayload = {
  years: number[];
  step: number;
  selectedYear: number;
};

export type LoadedMap = {
  year: number;
  map: CountryFeatureCollection;
  borders: GeoJSON.MultiLineString;
  regionBorders: GeoJSON.MultiLineString;
};
