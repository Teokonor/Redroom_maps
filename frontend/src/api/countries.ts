import type { Country } from '@/types/country';

const COUNTRIES_URL = 'http://127.0.0.1:8652/country/all';

let countriesPromise: Promise<Country[]> | null = null;

export function loadCountries(): Promise<Country[]> {
  if (!countriesPromise) {
    countriesPromise = fetch(COUNTRIES_URL)
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
