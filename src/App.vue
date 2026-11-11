<template>
  <header id="wmg-header" class="header">
    <router-link id="wmg-title" to="/" class="title">Wikimedia groups</router-link>
  </header>
  <main id="wmg-main">
    <router-view />
  </main>
</template>

<style scoped>
.header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 12px 16px;
}
.title {
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
}
</style>
