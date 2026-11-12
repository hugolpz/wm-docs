<template>
  <div id="wmg-wmfr" class="page">
    <AppBreadcrumb id="wmg-wmfr-breadcrumb" :items="crumbs" share-title="Wikimedia France spendings" />
    <Spendings />
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
