import { computed, ref, shallowRef, watch, type Ref } from 'vue';
import { loadCountries } from '@/api/countries';
import type { Country, CountryRegion } from '@/types/country';
import type { CountryShape } from '@/types/map';

export function useCountrySelection(
  selectedYear: Ref<number>,
  countryShapes: Ref<CountryShape[]>
) {
  const selectedCountryId = ref<string | null>(null);
  const isCountryPanelOpen = ref(false);
  const countries = shallowRef<Country[]>([]);

  let countriesPromise: Promise<void> | null = null;

  function ensureCountries() {
    if (!countriesPromise) {
      countriesPromise = loadCountries()
        .then((data) => {
          countries.value = data;
        })
        .catch((error) => {
          console.error('Ошибка загрузки стран', error);
          countriesPromise = null;
        });
    }
    return countriesPromise;
  }

  function selectCountry(id: string) {
    if (selectedCountryId.value === id) {
      if (isCountryPanelOpen.value) {
        clearSelection();
      } else {
        isCountryPanelOpen.value = true;
      }
    } else {
      selectedCountryId.value = id;
      isCountryPanelOpen.value = true;
    }

    if (selectedCountryId.value && countries.value.length === 0) {
      void ensureCountries();
    }
  }

  function clearSelection() {
    selectedCountryId.value = null;
    isCountryPanelOpen.value = false;
  }

  function closeCountryPanel() {
    isCountryPanelOpen.value = false;
  }

  const countriesById = computed(() => {
    const index = new Map<string, Country>();
    for (const country of countries.value) {
      index.set(country.id, country);
    }
    return index;
  });

  const selectedCountry = computed(() => {
    const id = selectedCountryId.value;
    return id ? countriesById.value.get(id) ?? null : null;
  });

  const selectedCountryShape = computed(() => {
    const id = selectedCountryId.value;
    return id
      ? countryShapes.value.find((shape) => shape.id === id) ?? null
      : null;
  });

  const selectedParentId = computed(() => {
    return (
      selectedCountryShape.value?.parent ??
      selectedCountry.value?.owner_id ??
      null
    );
  });

  const selectedParentName = computed(() => {
    const parentId = selectedParentId.value;
    if (!parentId) return null;

    return (
      countriesById.value.get(parentId)?.name ||
      countryShapes.value.find((shape) => shape.id === parentId)?.name ||
      parentId
    );
  });

  const selectedCountryRegions = computed<CountryRegion[]>(() => {
    const rootId = selectedCountryId.value;
    if (!rootId) return [];

    return countryShapes.value
      .filter((shape) => shape.parent === rootId)
      .map((shape) => ({
        id: shape.id,
        name: countriesById.value.get(shape.id)?.name || shape.name || shape.id,
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'ru'));
  });

  const selectedCountryShapes = computed(() => {
    const rootId = selectedCountryId.value;
    if (!rootId) return [];

    const shapes = countryShapes.value;
    const childrenByParent = new Map<string, CountryShape[]>();

    for (const shape of shapes) {
      if (!shape.parent) continue;
      const children = childrenByParent.get(shape.parent);
      if (children) children.push(shape);
      else childrenByParent.set(shape.parent, [shape]);
    }

    const selectedIds = new Set<string>([rootId]);
    const pending = [rootId];

    // Регионы могут быть вложены друг в друга, поэтому собираем всех потомков.
    while (pending.length > 0) {
      const parentId = pending.pop();
      if (parentId === undefined) continue;

      for (const child of childrenByParent.get(parentId) ?? []) {
        if (selectedIds.has(child.id)) continue;
        selectedIds.add(child.id);
        pending.push(child.id);
      }
    }

    return shapes.filter((shape) => selectedIds.has(shape.id));
  });

  const selectedHaloPath = computed(() =>
    selectedCountryShapes.value
      .map((shape) => shape.d)
      .filter(Boolean)
      .join(' ')
  );

  watch(selectedYear, () => {
    selectedCountryId.value = null;
    isCountryPanelOpen.value = false;
  });

  return {
    selectedCountryId,
    isCountryPanelOpen,
    selectCountry,
    clearSelection,
    closeCountryPanel,
    selectedCountry,
    selectedCountryShape,
    selectedParentId,
    selectedParentName,
    selectedCountryRegions,
    selectedCountryShapes,
    selectedHaloPath,
  };
}
