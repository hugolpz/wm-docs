<template>
  <div id="wmg-home">
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
.intro {
  color: var(--color-text-secondary);
}
.groups {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}
.groups a {
  font-weight: 600;
}
.groups p {
  margin: 4px 0 0;
  font-size: var(--fs-small);
  color: var(--color-text-secondary);
}
</style>
