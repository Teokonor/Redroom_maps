<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <div class="app-layout">
    <header class="main-header">
      <div class="header-left">
        <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="40" height="40" />
        <HelloWorld msg="You did it!" />
      </div>

      <nav class="main-nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav>
    </header>

    <main class="main-content">
      <RouterView />
    </main>
  </div>



  <!-- <div class="app-layout">
    <header>
      <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="25" height="25" />

      <div class="wrapper">
        <HelloWorld msg="You did it!" />

        <nav>
          <RouterLink to="/">Home</RouterLink>
          <RouterLink to="/about">About</RouterLink>
        </nav>
      </div>
    </header>

    <main>
      <RouterView />
    </main>
  </div> -->
</template>

<style scoped>
/* Главный контейнер на весь экран */
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #300000;
}

/* Узкая фиксированная шапка */
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 2rem;
  /* background-color: var(--color-background); */
  border-bottom: 1px solid var(--color-border);
  height: 60px; /* Фиксированная высота шапки */
}

/* Блок с логотипом и текстом */
.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  display: block;
}

/* Навигация справа */
.main-nav {
  display: flex;
  gap: 1rem;
  font-size: 1rem;
}

.main-nav a {
  text-decoration: none;
  color: var(--color-text);
  padding: 0.25rem 0.5rem;
}

.main-nav a.router-link-exact-active {
  color: var(--color-heading);
  font-weight: bold;
}

/* Контентная область занимает всё оставшееся место */
.main-content {
  flex-grow: 1;
  padding: 2rem;
  overflow-y: auto; /* Добавляет скролл только для контента, если он не влезает */
}



/* .app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 100vw;
}

main {
  flex-grow: 1;
  padding: 2rem;
  overflow-y: auto;
  background-color: #300000;
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 2rem;
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  height: 80px;
  line-height: 1.5;
  max-height: 100vh;
  background-color: #300000;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 0.8rem;

    padding: 1rem 0;
    margin-top: 0rem;
  }
} */
</style>
