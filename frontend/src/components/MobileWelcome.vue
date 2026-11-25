<script setup lang="ts">
import { onMounted, ref } from 'vue';

const emit = defineEmits<{
  close: [];
}>();

const closeButton = ref<HTMLButtonElement | null>(null);

onMounted(() => closeButton.value?.focus());
</script>

<template>
  <Teleport to="body">
    <div
      class="mobile-welcome-backdrop"
      role="presentation"
      @click.self="emit('close')"
    >
      <section
        class="mobile-welcome"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-welcome-title"
      >
        <button
          ref="closeButton"
          type="button"
          class="mobile-welcome-close"
          title="Закрыть"
          aria-label="Закрыть"
          @click="emit('close')"
        >
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2 2L10 10M10 2L2 10" />
          </svg>
        </button>

        <h2 id="mobile-welcome-title" class="mobile-welcome-title">
          Вас приветствует навигатор по видео канала Redroom.
        </h2>

        <ul class="mobile-welcome-list">
          <li>
            Кликнув на страну, увидите список видео про историю этой страны
          </li>
          <li>
            Кликнув на год сверху экрана, откроете панель выбора года — можно
            посмотреть карту разных лет
          </li>
          <li>
            Кликнув на кнопки сверху экрана, можете открыть меню с
            дополнительной информацией и настройки
          </li>
        </ul>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.mobile-welcome-backdrop {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 20px;
  background: rgba(0, 0, 0, 0.64);
}

.mobile-welcome {
  position: relative;
  box-sizing: border-box;
  width: min(420px, 100%);
  max-height: calc(100dvh - 40px);
  padding: 22px 20px;
  overflow-y: auto;
  color: #f4f0e6;
  background: #300000;
  border: 1px solid rgba(255, 216, 102, 0.42);
  border-radius: 14px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.mobile-welcome-title {
  margin: 0 0 14px;
  padding-right: 34px;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.3;
  color: #ffd866;
}

.mobile-welcome-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  font-size: 14px;
  line-height: 1.45;
  list-style: none;
}

.mobile-welcome-list li {
  position: relative;
  padding-left: 16px;
}

.mobile-welcome-list li::before {
  position: absolute;
  top: 0.55em;
  left: 0;
  width: 6px;
  height: 6px;
  content: '';
  background: #ffd866;
  border-radius: 50%;
}

.mobile-welcome-close {
  position: absolute;
  top: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  color: #f4f0e6;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
}

.mobile-welcome-close:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.4);
}

.mobile-welcome-close svg {
  display: block;
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
}

@media (max-width: 380px) {
  .mobile-welcome {
    padding: 18px 16px;
  }

  .mobile-welcome-title {
    font-size: 18px;
  }

  .mobile-welcome-list {
    font-size: 13px;
  }
}
</style>
