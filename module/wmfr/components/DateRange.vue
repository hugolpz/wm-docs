<template>
  <div v-if="quarters.length > 1" class="date-range-slider">
    <div class="slider-header">
      <span class="range-text">Range: <strong>{{ quarters[minValue].label }}</strong> to <strong>{{ quarters[maxValue].label }}</strong></span>
    </div>

    <div class="slider-body">
      <div class="range-container">
        <div class="range-selected" :style="selectedStyle"></div>
        <input
          v-model.number="minValue"
          type="range"
          class="slider-input"
          aria-label="First quarter"
          :min="0"
          :max="quarters.length - 1"
          @input="onInput('min')"
        />
        <input
          v-model.number="maxValue"
          type="range"
          class="slider-input"
          aria-label="Last quarter"
          :min="0"
          :max="quarters.length - 1"
          @input="onInput('max')"
        />
      </div>

      <div class="ticks">
        <span v-for="tick in ticks" :key="tick.label" :style="{ left: tick.pos + '%' }">{{ tick.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
// Local, self-contained quarter-step range filter for rows dated "YYYY/MM/DD".
// `from` / `to` are quarter labels ("2023Q1"); an empty or unknown one means the axis edge.
// It emits `change` with { from, to, range }: the labels to store in the URL ("" at an edge)
// fromLabel / toLabel = the selected quarters, edges included, and range = { from, to } (UTC Dates, inclusive), or null when the whole axis is selected.
import { computed, ref, watch } from 'vue';

const props = defineProps({
  // Rows to build the time axis from
  data: { type: Array, required: true },
  // Row field holding the date
  field: { type: String, default: 'Date' },
  from: { type: String, default: '' },
  to: { type: String, default: '' },
});

const emit = defineEmits(['change']);

// "2018/02/06" or "2018-02-06" -> UTC timestamp, NaN when unparseable
const toTime = (value) => {
  const m = String(value ?? '').match(/^(\d{4})[/-](\d{1,2})[/-](\d{1,2})/);
  return m ? Date.UTC(+m[1], +m[2] - 1, +m[3]) : NaN;
};

const quarters = computed(() => {
  const times = props.data.map((row) => toTime(row[props.field])).filter((t) => !isNaN(t));
  if (!times.length) return [];

  const min = new Date(Math.min(...times));
  const max = new Date(Math.max(...times));
  const first = min.getUTCFullYear() * 4 + Math.floor(min.getUTCMonth() / 3);
  const last = max.getUTCFullYear() * 4 + Math.floor(max.getUTCMonth() / 3);

  const result = [];
  for (let n = first; n <= last; n++) {
    const year = Math.floor(n / 4);
    const q = n % 4;
    result.push({
      label: `${year}Q${q + 1}`,
      start: new Date(Date.UTC(year, q * 3, 1)),
      end: new Date(Date.UTC(year, q * 3 + 3, 0, 23, 59, 59, 999)),
    });
  }
  return result;
});

const minValue = ref(0);
const maxValue = ref(0);

const isFullRange = computed(() => minValue.value === 0 && maxValue.value === quarters.value.length - 1);

const selectedStyle = computed(() => {
  const span = Math.max(1, quarters.value.length - 1);
  return {
    left: `${(minValue.value / span) * 100}%`,
    right: `${100 - (maxValue.value / span) * 100}%`,
  };
});

// About 8 labels, always including the last one
const ticks = computed(() => {
  const total = quarters.value.length;
  const step = Math.max(1, Math.floor(total / 8));
  const result = [];
  for (let i = 0; i < total; i += step) {
    result.push({ label: quarters.value[i].label, pos: (i / (total - 1)) * 100 });
  }
  if ((total - 1) % step !== 0) result.push({ label: quarters.value[total - 1].label, pos: 100 });
  return result;
});

// The two thumbs cannot cross
const onInput = (which) => {
  if (which === 'min' && minValue.value > maxValue.value) minValue.value = maxValue.value;
  if (which === 'max' && maxValue.value < minValue.value) maxValue.value = minValue.value;
  emitChange();
};

const emitChange = () => {
  const list = quarters.value;
  if (!list.length) return emit('change', { from: '', to: '', fromLabel: '', toLabel: '', range: null });
  const last = list.length - 1;
  emit('change', {
    from: minValue.value === 0 ? '' : list[minValue.value].label,
    to: maxValue.value === last ? '' : list[maxValue.value].label,
    fromLabel: list[minValue.value].label,
    toLabel: list[maxValue.value].label,
    range: isFullRange.value ? null : { from: list[minValue.value].start, to: list[maxValue.value].end },
  });
};

// Labels -> thumb positions; returns true when a thumb moved
const applyProps = () => {
  const list = quarters.value;
  const last = Math.max(0, list.length - 1);
  const lo = Math.max(0, list.findIndex((q) => q.label === props.from));
  const hiIdx = list.findIndex((q) => q.label === props.to);
  const hi = hiIdx === -1 ? last : hiIdx;
  const [min, max] = lo <= hi ? [lo, hi] : [hi, lo];
  const moved = min !== minValue.value || max !== maxValue.value;
  minValue.value = min;
  maxValue.value = max;
  return moved;
};

// New axis: apply from/to (all selected when unset)
watch(
  quarters,
  () => {
    applyProps();
    emitChange();
  },
  { immediate: true },
);

// URL changed from outside (back/forward, pasted link)
watch(() => [props.from, props.to], () => {
  if (applyProps()) emitChange();
});
</script>

<style scoped>
.date-range-slider {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 0.5rem 1rem;
  margin: 0.5rem 0 1rem 0;
  padding: 0 10px;
}

.slider-header {
  flex: none;
  font-size: 0.9rem;
  line-height: 18px; /* aligns with the thumbs */
  color: var(--color-text);
}

.slider-body {
  flex: 1 1 16rem;
  min-width: 0;
  padding: 0 1.5rem; /* room for the first/last tick labels */
}

.range-container {
  position: relative;
  height: 6px;
  background: var(--color-surface-muted);
  border-radius: 3px;
  margin: 6px 0 0; /* thumbs overflow the track by 6px */
}

.range-selected {
  position: absolute;
  top: 0;
  bottom: 0;
  background: var(--color-progressive);
  border-radius: 3px;
}

.slider-input {
  position: absolute;
  top: -6px;
  width: 100%;
  height: 18px;
  margin: 0;
  background: none;
  pointer-events: none;
  appearance: none;
}

.slider-input::-webkit-slider-thumb {
  pointer-events: auto;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--color-surface);
  border: 2px solid var(--color-progressive);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: var(--shadow);
}

.slider-input::-moz-range-thumb {
  pointer-events: auto;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--color-surface);
  border: 2px solid var(--color-progressive);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: var(--shadow);
}

.ticks {
  position: relative;
  height: 14px;
  margin-top: 0.5rem;
}

.ticks span {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--color-text-muted);
  white-space: nowrap;
}
</style>
