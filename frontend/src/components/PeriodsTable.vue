<script setup lang="ts">
import { computed, ref } from 'vue';
import type { PeriodRow } from '@/types/period';
import { toDisplayYear } from '@/utils/yearLabels';

const props = defineProps<{
  rows: PeriodRow[];
}>();

type SortKey = 'begin' | 'end' | 'country';

const sortKey = ref<SortKey>('begin');
const sortAscending = ref(true);

const sortedRows = computed<PeriodRow[]>(() => {
  const nextRows = [...props.rows];
  const direction = sortAscending.value ? 1 : -1;

  nextRows.sort((a, b) => {
    let result = 0;

    if (sortKey.value === 'country') {
      result = a.countryName.localeCompare(b.countryName, 'ru');
    } else if (sortKey.value === 'begin') {
      result = a.beginYear - b.beginYear;
    } else {
      result = a.endYear - b.endYear;
    }

    if (result === 0) {
      result =
        a.beginYear - b.beginYear ||
        a.endYear - b.endYear ||
        a.countryName.localeCompare(b.countryName, 'ru');
    }

    return result * direction;
  });

  return nextRows;
});

function ariaSort(key: SortKey): 'ascending' | 'descending' | 'none' {
  if (sortKey.value !== key) return 'none';
  return sortAscending.value ? 'ascending' : 'descending';
}

function toggleSort(key: SortKey) {
  if (sortKey.value === key) {
    sortAscending.value = !sortAscending.value;
    return;
  }

  sortKey.value = key;
  sortAscending.value = true;
}
</script>

<template>
  <table class="periods-table">
    <thead>
      <tr>
        <th class="periods-year-column" :aria-sort="ariaSort('begin')">
          <button
            type="button"
            class="periods-sort"
            @click="toggleSort('begin')"
          >
            <span>Год начала</span>
            <span
              v-if="sortKey === 'begin'"
              class="periods-sort-arrow"
              aria-hidden="true"
            >
              {{ sortAscending ? '↑' : '↓' }}
            </span>
          </button>
        </th>
        <th class="periods-year-column" :aria-sort="ariaSort('end')">
          <button
            type="button"
            class="periods-sort"
            @click="toggleSort('end')"
          >
            <span>Год окончания</span>
            <span
              v-if="sortKey === 'end'"
              class="periods-sort-arrow"
              aria-hidden="true"
            >
              {{ sortAscending ? '↑' : '↓' }}
            </span>
          </button>
        </th>
        <th :aria-sort="ariaSort('country')">
          <button
            type="button"
            class="periods-sort"
            @click="toggleSort('country')"
          >
            <span>Страна</span>
            <span
              v-if="sortKey === 'country'"
              class="periods-sort-arrow"
              aria-hidden="true"
            >
              {{ sortAscending ? '↑' : '↓' }}
            </span>
          </button>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="(row, index) in sortedRows"
        :key="`${row.countryId}-${row.beginYear}-${row.endYear}-${index}`"
      >
        <td class="periods-year">{{ toDisplayYear(row.beginYear) }}</td>
        <td class="periods-year">{{ toDisplayYear(row.endYear) }}</td>
        <td class="periods-country">{{ row.countryName }}</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.periods-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  line-height: 1.4;
}

.periods-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 0;
  text-align: left;
  background: #300000;
  border-bottom: 1px solid rgba(255, 216, 102, 0.32);
}

.periods-sort {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  width: 100%;
  padding: 8px 10px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  color: rgba(244, 240, 230, 0.82);
  text-align: left;
  cursor: pointer;
  background: transparent;
  border: 0;
}

.periods-sort:hover {
  color: #ffd866;
}

.periods-sort-arrow {
  font-size: 12px;
  color: #ffd866;
}

.periods-table td {
  padding: 7px 10px;
  vertical-align: top;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.periods-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.06);
}

.periods-year {
  width: 1%;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  color: rgba(244, 240, 230, 0.92);
}

.periods-country {
  color: rgba(244, 240, 230, 0.86);
  overflow-wrap: anywhere;
}
</style>
