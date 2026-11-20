import { API_URL } from '@/api/base';
import { withDataVersion } from '@/api/version';
import type { Country } from '@/types/country';

const COUNTRIES_URL = `${API_URL}/country/all`;

let countriesPromise: Promise<Country[]> | null = null;

export function loadCountries(): Promise<Country[]> {
  if (!countriesPromise) {
    countriesPromise = withDataVersion(COUNTRIES_URL)
      .then((url) => fetch(url))
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Не удалось загрузить страны: ${response.status}`);
        }
        return response.json() as Promise<Country[]>;
      })
      .catch((error) => {
        countriesPromise = null;
        throw error;
      });
  }

  return countriesPromise;
}
