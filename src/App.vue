<template>
  <header id="wmg-header" class="header">
    <router-link id="wmg-title" to="/" class="title">Wikimedia groups</router-link>
    <button id="wmg-theme-toggle" type="button" class="theme-toggle" aria-label="Toggle dark theme" :title="isDark ? 'Light theme' : 'Dark theme'" @click="toggleTheme">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path :d="isDark ? SUN : MOON" />
      </svg>
    </button>
  </header>
  <main id="wmg-main">
    <router-view />
  </main>
  <ToolCounter id="wmg-toolcounter" :page="String(route.name || 'home')" />
</template>

<script setup>
import { useRoute } from 'vue-router';
import { ref } from 'vue';
import ToolCounter from './components/ToolCounter.vue';
import { applyTheme, currentTheme } from './theme.js';

// Material Design Icons paths
const SUN = 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10m0-5 2 3h-4zm0 20-2-3h4zM2 12l3-2v4zm20 0-3 2v-4zM4.9 4.9l3.5.9-2.6 2.6zm14.2 14.2-3.5-.9 2.6-2.6zM4.9 19.1l.9-3.5 2.6 2.6zM19.1 4.9l-.9 3.5-2.6-2.6z';
const MOON = 'M17.75 4.09l-2.53 1.94.91 3.06-2.63-1.81-2.63 1.81.91-3.06-2.53-1.94L12.44 4l1.06-3 1.06 3zm3.5 6.91l-1.64 1.25.59 1.98-1.7-1.17-1.7 1.17.59-1.98L15.75 11l2.06-.05L18.5 9l.69 1.95zm-2.28 4.95c.83-.08 1.72 1.1 1.19 1.85-.32.45-.66.87-1.08 1.27C15.17 23 8.84 23 4.94 19.07c-3.91-3.9-3.91-10.24 0-14.14.4-.4.82-.76 1.27-1.08.75-.53 1.93.36 1.85 1.19-.27 2.86.69 5.83 2.89 8.02a9.96 9.96 0 0 0 8.02 2.89';

const isDark = ref(currentTheme() === 'dark');
const toggleTheme = () => {
  applyTheme(isDark.value ? 'light' : 'dark');
  isDark.value = !isDark.value;
};

const route = useRoute();
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 12px 16px;
}
.theme-toggle {
  display: inline-flex;
  align-items: center;
  padding: 4px;
  border: 0;
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
}
.title {
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}
</style>
