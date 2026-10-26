export type CountryBase = {
  id: string;
  name: string;
  begin_year: number;
  end_year: number | null;
  owner_id: string | null;
  deleted: boolean;
};

export type Country = CountryBase & {
  owner: CountryBase | null;
  regions: CountryBase[];
};

export type CountryRegion = {
  id: string;
  name: string;
};
