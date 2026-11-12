<template>
  <div id="wmg-home" class="page">
    <h1 id="wmg-home-title">Wikimedia groups</h1>
    <p class="intro">Searchable data published by Wikimedia groups.</p>
    <ul id="wmg-home-groups" class="groups">
      <li v-for="g in groups" :id="`wmg-home-groups-${g.slug}`" :key="g.slug" class="card">
        <router-link :to="`/${g.slug}`">{{ g.name }}</router-link>
        <p>{{ g.description }}</p>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { groups } from '../groups.js'
</script>

<style scoped>
#wmg-home-title {
  margin: 8px 0 4px;
  font-size: 2rem;
  line-height: 1.2;
}
.intro {
  margin: 0 0 24px;
  font-size: 1.1rem;
  color: var(--color-text-secondary);
}
.groups {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}
.card {
  position: relative; /* anchors the stretched link below */
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.card:hover,
.card:focus-within {
  border-color: var(--color-progressive);
  box-shadow: var(--shadow-card);
}
.groups a {
  font-weight: 600;
  font-size: 1.1rem;
}
/* The whole card is clickable */
.groups a::after {
  content: '';
  position: absolute;
  inset: 0;
}
.groups p {
  margin: 4px 0 0;
  font-size: var(--fs-small);
  color: var(--color-text-secondary);
}
</style>
