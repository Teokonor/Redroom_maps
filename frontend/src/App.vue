<script setup lang="ts">
import { ref } from 'vue';
import { RouterView } from 'vue-router';
import TopPanel from '@/components/TopPanel.vue';

type Panel = 'collections' | 'help' | 'support';

const panels: Array<{ id: Panel; label: string }> = [
  { id: 'collections', label: 'Подборки' },
  { id: 'help', label: 'Справка' },
  { id: 'support', label: 'Поддержать' },
];

const activePanel = ref<Panel | null>(null);

function togglePanel(panel: Panel) {
  activePanel.value = activePanel.value === panel ? null : panel;
}

function closePanel() {
  activePanel.value = null;
}
</script>

<template>
  <div class="app-layout">
    <header class="main-header">
      <nav class="main-nav" aria-label="Основное меню">
        <button
          v-for="panel in panels"
          :key="panel.id"
          type="button"
          class="header-button"
          :class="{ 'is-active': activePanel === panel.id }"
          @click="togglePanel(panel.id)"
        >
          {{ panel.label }}
        </button>
      </nav>

      <div id="projection-slot" class="projection-slot"></div>
    </header>

    <main class="main-content">
      <RouterView />
    </main>

    <TopPanel
      v-if="activePanel"
      :panel="activePanel"
      @close="closePanel"
    />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #300000;
}

.main-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: flex-start;
  height: 60px;
  padding: 0.5rem 2rem;
  border-bottom: 1px solid var(--color-border);
}

.main-nav {
  display: flex;
  gap: 8px;
}

.projection-slot {
  display: flex;
  align-items: center;
  min-width: 0;
  margin-left: auto;
}

.header-button {
  padding: 8px 14px;
  font: inherit;
  font-size: 14px;
  line-height: 1.2;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 6px;
  transition:
    background 0.15s,
    border-color 0.15s,
    color 0.15s;
}

.header-button:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.36);
}

.header-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.main-content {
  flex-grow: 1;
  padding: 2rem;
  overflow-y: auto;
}
</style>
