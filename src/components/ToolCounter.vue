<template>
  <!-- The parent passes `id` (falls through to this root), e.g. <ToolCounter id="wmg-toolcounter" /> -->
  <div ref="root" class="toolcounter">
    <!-- `toolcounter`, `tc-views` and `tc-sessions` are required by embed.js.php, do not rename -->
    <p id="toolcounter" style="opacity: 0">
      <span id="tc-views"></span>
      <span id="tc-sessions"></span>
    </p>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({
  tool: { type: String, default: 'wm-docs' },
  // Counted page name, e.g. the route name: "wmfr"
  page: { type: String, required: true },
  style: { type: String, default: 'badge' },
});

const root = ref(null);
let script = null;

// <script> tags inside a Vue template never run, so the embed is injected by hand.
// The app is a SPA: re-inject it on each route change so the new page is counted.
function load() {
  unload();
  if (!props.page) return;
  const query = new URLSearchParams({ tool: props.tool, page: props.page, style: props.style });
  script = document.createElement('script');
  script.src = `https://toolcounter.toolforge.org/embed.js.php?${query}`;
  script.async = true;
  root.value?.appendChild(script);
}

function unload() {
  script?.remove();
  script = null;
}

onMounted(load);
watch(() => props.page, load);
onBeforeUnmount(unload);
</script>

<style scoped>
.toolcounter {
  padding: 12px 16px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted, inherit);
}
</style>
