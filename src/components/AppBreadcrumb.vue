<template>
  <nav class="crumbs" aria-label="Breadcrumb">
    <template v-for="(item, i) in crumbs" :key="i">
      <span v-if="i > 0" aria-hidden="true">›</span>
      <router-link v-if="item.link" :id="item.id" :to="item.to">{{ item.label }}</router-link>
      <span v-else :id="item.id" class="current" :aria-current="item.current ? 'page' : undefined">{{ item.label }}</span>
    </template>
  </nav>
</template>

<script setup>
// Standalone stand-in for lingua-deck's AppBreadcrumb (same `items` prop; no share button).
// A crumb is a link only if its route exists here, so lingua-deck's "Transparency" crumb is plain text.
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({ items: { type: Array, required: true }, shareTitle: { type: String, default: '' } })
const route = useRoute()
const router = useRouter()

const crumbs = computed(() =>
  props.items.map((item, i) => {
    const target = item.to ? router.resolve(item.to) : null
    const current = i === props.items.length - 1 || target?.fullPath === route.fullPath
    return { ...item, current, link: !!target?.matched.length && !current }
  }),
)
</script>

<style scoped>
.crumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-small);
}
.current {
  font-weight: 600;
}
</style>
