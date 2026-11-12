<template>
  <nav class="crumbs" aria-label="Breadcrumb">
    <template v-for="(item, i) in crumbs" :key="i">
      <span v-if="i > 0" aria-hidden="true">›</span>
      <router-link v-if="item.link" :id="item.id" :to="item.to">{{ item.label }}</router-link>
      <span v-else :id="item.id" class="current" :aria-current="item.current ? 'page' : undefined">{{ item.label }}</span>
    </template>
    <button type="button" class="share" :title="shared ? 'Link copied' : shareLabel" :aria-label="shareLabel" @click="share">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline v-if="shared" points="20 6 9 17 4 12" />
        <template v-else>
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.6" y1="13.5" x2="15.4" y2="17.5" />
          <line x1="15.4" y1="6.5" x2="8.6" y2="10.5" />
        </template>
      </svg>
    </button>
    <span v-if="$slots.default" class="sep">·</span>
    <slot />
  </nav>
</template>

<script setup>
// Standalone stand-in for lingua-deck's AppBreadcrumb (same props, share button with inline icons).
// A crumb is a link only if its route exists here, so lingua-deck's "Transparency" crumb is plain text.
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  items: { type: Array, required: true },
  /** URL or route location to share. Defaults to the current page. */
  shareUrl: { type: [String, Object], default: null },
  shareLabel: { type: String, default: 'Share this page' },
  shareTitle: { type: String, default: '' },
})
const route = useRoute()
const router = useRouter()

const crumbs = computed(() =>
  props.items.map((item, i) => {
    const target = item.to ? router.resolve(item.to) : null
    const current = i === props.items.length - 1 || target?.fullPath === route.fullPath
    return { ...item, current, link: !!target?.matched.length && !current }
  }),
)

const shared = ref(false)

// encodeURIComponent leaves ! ' ( ) * as is; filters can be regexes like (a|b)* so encode them too
const encode = (v) => encodeURIComponent(v).replace(/[!'()*]/g, (c) => '%' + c.charCodeAt(0).toString(16).toUpperCase())

// Hash history: the app lives after "#", so rebuild "#/path?key=value" with every key and value fully encoded
const buildUrl = (location) => {
  const { path, query, hash } = router.resolve(location)
  const qs = Object.entries(query)
    .flatMap(([k, v]) => (Array.isArray(v) ? v : [v]).map((x) => (x == null ? encode(k) : `${encode(k)}=${encode(String(x))}`)))
    .join('&')
  return window.location.href.split('#')[0] + '#' + path + (qs ? '?' + qs : '') + hash
}

const share = async () => {
  const url = buildUrl(props.shareUrl ?? route.fullPath)
  try {
    if (navigator.share) {
      await navigator.share({ title: props.shareTitle || document.title, url })
      return
    }
    await navigator.clipboard.writeText(url)
    shared.value = true
    setTimeout(() => (shared.value = false), 2000)
  } catch {
    // share sheet dismissed or clipboard unavailable: nothing to do
  }
}
</script>

<style scoped>
.crumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--fs-small);
}
.crumbs {
  align-items: baseline;
}
.share {
  display: inline-flex;
  align-items: center;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-text-muted, inherit);
  cursor: pointer;
}
.share:hover {
  color: inherit;
}
.sep {
  color: var(--color-text-muted, inherit);
}
.current {
  font-weight: 600;
}
</style>
