<script setup lang="ts">
import SocialIcon from '@/components/icons/SocialIcon.vue';
</script>

<template>
  <div class="help">
    <p>Этот сайт - навигатор по контенту ютуб-канала Redroom.</p>

    <p>
      На карте можно выбрать любую страну и увидеть подборку видео про неё за
      конкретный год или за всю историю. Можно переключать выбранный год в
      панели годов. Доступно три масштаба: каждые 100 лет, каждые 10 и каждый 1.
      Можно скроллить или листать нажимая кнопки.
    </p>

    <p>
      Много где отмечены не только страны, но и их отдельные регионы. По дефолту
      их границы не видны, но можно включить их в переключателе "Границы
      регионов" (довольно логично, не так ли?) Ещё можно поменять используемую
      проекцию карты, как вам такое? Мб когда-нибудь ещё глобус сделаю, но это
      посложнее задачка.
    </p>

    <p>
      Качество видео это по сути просто информация о годе выхода. Всё, что до 
      трейлера канала идёт по градиенту от плохого к хорошему, всё что позже по 
      умолчанию считается хорошим.
    </p>

    <p>
      У приложения есть мобильная версия. Шкала выбора года открывается по 
      нажатию на год сверху. Закрыть: повторное нажатие, либо крестик. Изменять 
      масштаб шкалы можно движениями пальцев (как приближение на карте), либо 
      кнопками.
    </p>

    <p>
      В меню "Подборки" доступна выборка видео по категориям. Не все видео
      канала про конкретный период конкретной страны - иногда это большой
      экскурс по какой-то теме, такие проще найти в подборке по этой самой теме.
      История причёсок Егора обязательно будет чуть позже)
    </p>

    <p>
      В меню "Идеи" список всех "Достойных отдельного выпуска", о которых
      говорилось в видео, но которые ещё пока не выпущены.
    </p>

    <p class="help-contact">
      Если есть какие-то вопросы или предложения по улучшению проекта, пишите в
      лс сообществ:
    </p>

    <ul class="help-links">
      <li>
        <a
          class="help-link"
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
          class="help-link"
          href="https://vk.ru/Redroom_maps"
          target="_blank"
          rel="noopener noreferrer"
        >
          <SocialIcon brand="vk" />
          <span>vk.ru/Redroom_maps</span>
        </a>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.help {
  box-sizing: border-box;
  height: 100%;
  padding-right: 12px;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.help p {
  margin: 0 0 14px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(244, 240, 230, 0.82);
  overflow-wrap: anywhere;
}

.help p:last-of-type {
  margin-bottom: 10px;
}

.help-contact {
  margin-bottom: 8px !important;
}

.help-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.help-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 1.4;
  color: #ffd866;
  text-decoration: none;
  overflow-wrap: anywhere;
}

.help-link:hover {
  text-decoration: underline;
}
</style>
