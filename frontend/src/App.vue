<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { RouterView } from 'vue-router';
import MobileWelcome from '@/components/MobileWelcome.vue';
import TopPanel from '@/components/TopPanel.vue';
import { useMapState } from '@/composables/useMapState';
import { useMobileLayout } from '@/composables/useMobileLayout';
import { formatYearHuman } from '@/utils/yearLabels';

const MOBILE_WELCOME_KEY = 'redroom:mobile-welcome-v1';

type Panel = 'collections' | 'ideas' | 'help' | 'contacts';

const panels: Array<{ id: Panel; label: string }> = [
  { id: 'collections', label: 'Подборки' },
  { id: 'ideas', label: 'Идеи' },
  { id: 'help', label: 'Справка' },
  { id: 'contacts', label: 'Контакты' },
];

const isMobile = useMobileLayout();
const {
  projectionOptions,
  selectedYear,
  isYearRulerOpen,
  selectedProjectionId,
  showRegionBorders,
  showIndirectVideos,
  isSettingsOpen,
} = useMapState();

const activePanel = ref<Panel | null>(null);
const mobileMenuOpen = ref(false);
const showMobileWelcome = ref(false);

function hasSeenMobileWelcome(): boolean {
  if (typeof window === 'undefined') return true;

  try {
    return window.localStorage.getItem(MOBILE_WELCOME_KEY) === '1';
  } catch {
    return true;
  }
}

function closeMobileWelcome() {
  showMobileWelcome.value = false;

  try {
    window.localStorage.setItem(MOBILE_WELCOME_KEY, '1');
  } catch {
    // Storage can be unavailable in private mode.
  }
}

function togglePanel(panel: Panel) {
  activePanel.value = activePanel.value === panel ? null : panel;
}

function closePanel() {
  activePanel.value = null;
}

function openMobilePanel(panel: Panel) {
  activePanel.value = panel;
  mobileMenuOpen.value = false;
  isSettingsOpen.value = false;
  isYearRulerOpen.value = false;
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value;
  if (mobileMenuOpen.value) isSettingsOpen.value = false;
}

function toggleMobileSettings() {
  isSettingsOpen.value = !isSettingsOpen.value;
  if (isSettingsOpen.value) mobileMenuOpen.value = false;
}

function toggleYearRuler() {
  const panelClose = document.querySelector<HTMLButtonElement>(
    '.country-panel .country-panel-close'
  );
  const panelWasOpen = panelClose !== null;

  if (panelClose) {
    panelClose.click();
  }

  isYearRulerOpen.value = panelWasOpen
    ? true
    : !isYearRulerOpen.value;

  if (isYearRulerOpen.value) {
    mobileMenuOpen.value = false;
    isSettingsOpen.value = false;
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (!isMobile.value || event.key !== 'Escape') return;

  if (showMobileWelcome.value) {
    closeMobileWelcome();
    return;
  }

  if (
    document.querySelector(
      '.video-details-backdrop, .periods-backdrop'
    )
  ) {
    return;
  }

  if (mobileMenuOpen.value) {
    mobileMenuOpen.value = false;
  } else if (isSettingsOpen.value) {
    isSettingsOpen.value = false;
  } else if (isYearRulerOpen.value) {
    isYearRulerOpen.value = false;
  } else if (activePanel.value) {
    activePanel.value = null;
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown);

  if (isMobile.value && !hasSeenMobileWelcome()) {
    showMobileWelcome.value = true;
  }
});

watch(isMobile, (mobile) => {
  if (mobile && !hasSeenMobileWelcome()) {
    showMobileWelcome.value = true;
  }
});

onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown));
</script>

<template>
  <div class="app-layout" :class="{ 'is-mobile': isMobile }">
    <header v-show="isMobile" class="mobile-header">
      <button
        type="button"
        class="mobile-icon-button"
        title="Меню"
        aria-label="Меню"
        @click="toggleMobileMenu"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>

      <button
        type="button"
        class="mobile-year-button"
        :class="{ 'is-active': isYearRulerOpen }"
        title="Выбрать год"
        @click="toggleYearRuler"
      >
        {{ formatYearHuman(selectedYear) }}
      </button>

      <button
        type="button"
        class="mobile-icon-button"
        :class="{ 'is-active': isSettingsOpen }"
        title="Настройки карты"
        aria-label="Настройки карты"
        @click="toggleMobileSettings"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 0 1 0 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 0 1 0-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.077-.124.072-.044.146-.086.22-.128.331-.183.581-.495.644-.869l.213-1.281Z"
          />
          <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
        </svg>
      </button>
    </header>

    <header v-show="!isMobile" class="main-header">
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

    <div
      v-if="isMobile && mobileMenuOpen"
      class="mobile-menu"
      role="dialog"
      aria-modal="true"
      aria-label="Меню"
    >
      <div class="mobile-menu-header">
        <span class="mobile-menu-title">Меню</span>
        <button
          type="button"
          class="mobile-icon-button"
          title="Закрыть"
          aria-label="Закрыть"
          @click="mobileMenuOpen = false"
        >
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2 2L10 10M10 2L2 10" />
          </svg>
        </button>
      </div>

      <nav class="mobile-menu-list" aria-label="Разделы">
        <button
          v-for="panel in panels"
          :key="panel.id"
          type="button"
          class="mobile-menu-item"
          @click="openMobilePanel(panel.id)"
        >
          {{ panel.label }}
        </button>
      </nav>
    </div>

    <div
      v-if="isMobile && isSettingsOpen"
      class="mobile-settings-backdrop"
      @click.self="isSettingsOpen = false"
    >
      <div
        class="mobile-settings"
        role="dialog"
        aria-modal="true"
        aria-label="Настройки карты"
      >
        <label class="mobile-region-toggle">
          <input v-model="showRegionBorders" type="checkbox" />
          <span>Границы регионов</span>
        </label>

        <label class="mobile-region-toggle">
          <input v-model="showIndirectVideos" type="checkbox" />
          <span>Косвенно упомянутые</span>
        </label>

        <div class="mobile-settings-title">Проекция</div>
        <div class="mobile-projection-list">
          <button
            v-for="option in projectionOptions"
            :key="option.id"
            type="button"
            class="mobile-projection-button"
            :class="{ 'is-active': selectedProjectionId === option.id }"
            @click="selectedProjectionId = option.id"
          >
            {{ option.label }}
          </button>
        </div>
      </div>
    </div>

    <MobileWelcome
      v-if="isMobile && showMobileWelcome"
      @close="closeMobileWelcome"
    />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-height: 0;
  overflow: hidden;
  background-color: #300000;
}

.app-layout.is-mobile {
  --mobile-header-height: calc(52px + env(safe-area-inset-top));
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
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
  flex: 1 1 auto;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.is-mobile .main-content {
  flex: 1 1 auto;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.mobile-header {
  position: relative;
  z-index: 10;
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  height: var(--mobile-header-height);
  padding: env(safe-area-inset-top) 8px 0;
  background: #300000;
  border-bottom: 1px solid rgba(255, 216, 102, 0.22);
}

.mobile-icon-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 7px;
}

.mobile-icon-button:hover,
.mobile-icon-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.mobile-icon-button svg {
  display: block;
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.mobile-year-button {
  flex: 0 1 auto;
  min-width: 0;
  padding: 9px 16px;
  overflow: hidden;
  font: inherit;
  font-size: 15px;
  line-height: 1.2;
  color: #f4f0e6;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 7px;
}

.mobile-year-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}

.mobile-menu {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
  padding: calc(12px + env(safe-area-inset-top)) 12px
    calc(12px + env(safe-area-inset-bottom));
  color: #f4f0e6;
  background: #300000;
}

.mobile-menu-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
}

.mobile-menu-title {
  font-size: 22px;
  font-weight: 600;
  color: #ffd866;
}

.mobile-menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-menu-item {
  width: 100%;
  padding: 15px 14px;
  font: inherit;
  font-size: 17px;
  line-height: 1.3;
  color: #f4f0e6;
  text-align: left;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 8px;
}

.mobile-menu-item:hover {
  background: rgba(255, 255, 255, 0.14);
}

.mobile-settings-backdrop {
  position: fixed;
  top: var(--mobile-header-height);
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 39;
  background: rgba(0, 0, 0, 0.28);
}

.mobile-settings {
  position: absolute;
  top: 8px;
  right: 8px;
  box-sizing: border-box;
  width: min(320px, calc(100vw - 16px));
  max-height: calc(100dvh - var(--mobile-header-height) - 24px);
  padding: 14px;
  overflow-y: auto;
  color: #f4f0e6;
  background: #300000;
  border: 1px solid rgba(255, 216, 102, 0.36);
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}

.mobile-region-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
  font-size: 14px;
  line-height: 1.3;
  cursor: pointer;
}

.mobile-region-toggle input {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: #ffd866;
}

.mobile-settings-title {
  margin: 10px 4px 8px;
  font-size: 12px;
  letter-spacing: 0.05em;
  color: rgba(244, 240, 230, 0.6);
  text-transform: uppercase;
}

.mobile-projection-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mobile-projection-button {
  width: 100%;
  padding: 10px 12px;
  font: inherit;
  font-size: 14px;
  line-height: 1.2;
  color: #f4f0e6;
  text-align: left;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 6px;
}

.mobile-projection-button.is-active {
  color: #000035;
  background: #ffd866;
  border-color: #ffd866;
}
</style>
