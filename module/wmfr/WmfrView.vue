<template>
  <div id="wmg-wmfr" class="page">
    <AppBreadcrumb id="wmg-wmfr-breadcrumb" :items="crumbs" share-title="Wikimedia France spendings" />
    <section id="wmg-wmfr-budget" class="budget-section card mb-12 p-4">
      <Spendings />
    </section>
  </div>
</template>

<script setup>
import AppBreadcrumb from '@/components/AppBreadcrumb.vue';
import Spendings from './components/Spendings.vue';

const crumbs = [
  { label: 'Transparency', to: '/transparency' },
  { label: 'Wikimedia France', to: '/transparency/wmfr' },
];
</script>
