<script setup lang="ts">
import SocialIcon from '@/components/icons/SocialIcon.vue';
</script>

<template>
  <div class="contacts">
    <section class="contacts-section">
      <h3 class="contacts-title">Поддержать канал Redroom</h3>
      <ul class="contacts-links">
        <li>
          <a
            class="contacts-link"
            href="https://patreon.com/c/redroomlimb"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="patreon" />
            <span>patreon.com/c/redroomlimb</span>
          </a>
        </li>
        <li>
          <a
            class="contacts-link"
            href="https://boosty.to/redroomlimb"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="boosty" />
            <span>boosty.to/redroomlimb</span>
          </a>
        </li>
      </ul>
    </section>

    <section class="contacts-section">
      <h3 class="contacts-title">Поддержать админа сайта</h3>
      <ul class="contacts-links">
        <li>
          <a
            class="contacts-link"
            href="https://boosty.to/redroom_maps"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="boosty" />
            <span>https://boosty.to/redroom_maps</span>
          </a>
        </li>
      </ul>
    </section>

    <section class="contacts-section">
      <h3 class="contacts-title">
        Предложения по улучшению сайта (лс сообщества)
      </h3>
      <ul class="contacts-links">
        <li>
          <a
            class="contacts-link"
            href="https://t.me/Redroom_maps"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="telegram" />
            <span>t.me/Redroom_maps</span>
          </a>
        </li>
        <li>
          <a
            class="contacts-link"
            href="https://vk.ru/Redroom_maps"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="vk" />
            <span>vk.ru/Redroom_maps</span>
          </a>
        </li>
      </ul>
    </section>

    <section class="contacts-section">
      <h3 class="contacts-title">
        Делаю сайты и программы на заказ. Пишите в лс, договоримся
      </h3>
      <ul class="contacts-links">
        <li>
          <a
            class="contacts-link"
            href="https://t.me/Lembocoder"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SocialIcon brand="telegram" />
            <span>t.me/Lembocoder</span>
          </a>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.contacts {
  box-sizing: border-box;
  height: 100%;
  padding-right: 12px;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.contacts-section + .contacts-section {
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.contacts-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: rgba(244, 240, 230, 0.95);
  overflow-wrap: anywhere;
}

.contacts-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0 0 14px;
  padding: 0;
  list-style: none;
}

.contacts-section:last-child .contacts-links {
  margin-bottom: 0;
}

.contacts-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 1.4;
  color: #ffd866;
  text-decoration: none;
  overflow-wrap: anywhere;
}

.contacts-link:hover {
  text-decoration: underline;
}
</style>
