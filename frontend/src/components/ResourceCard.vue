<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from 'frappe-ui'
import type { CalendarCard, FieldStyle } from '@/types'
import { cardColor } from '@/utils/colors'

const props = defineProps<{
  card: CalendarCard
  canWrite: boolean
  dragging?: boolean
  continuesBefore?: boolean
  continuesAfter?: boolean
  /** Horizontal / vertical offset while the card is being dragged. */
  offsetX?: number
  offsetY?: number
}>()
const emit = defineEmits<{
  (e: 'press', event: PointerEvent, mode: 'move' | 'left' | 'right'): void
  (e: 'open'): void
}>()

const color = computed(() => cardColor(props.card.color))

const lineClass: Record<FieldStyle, string> = {
  Normal: '',
  Bold: 'font-semibold',
  Muted: 'opacity-65',
  Italic: 'italic',
  Badge: '',
}
</script>

<template>
  <div
    role="button"
    tabindex="0"
    class="group relative h-full select-none overflow-visible border-l-4 px-2.5 py-1.5 text-left outline-none transition-shadow focus-visible:ring-2 focus-visible:ring-outline-gray-4"
    :class="[
      canWrite ? 'cursor-grab' : 'cursor-pointer',
      dragging ? 'z-30 cursor-grabbing opacity-90 shadow-xl ring-2 ring-outline-gray-4' : 'hover:shadow-md',
      continuesBefore ? 'rounded-l-none' : 'rounded-l-md',
      continuesAfter ? 'rounded-r-none' : 'rounded-r-md',
    ]"
    :style="{
      backgroundColor: color.bg,
      borderLeftColor: color.accent,
      color: color.text,
      transform: dragging ? `translate(${offsetX ?? 0}px, ${offsetY ?? 0}px)` : undefined,
    }"
    :title="`${card.title}\n${card.start} → ${card.end}`"
    @pointerdown.left.prevent="emit('press', $event, 'move')"
    @keydown.enter.prevent="emit('open')"
  >
    <span
      v-if="canWrite"
      class="absolute inset-y-0 left-0 z-10 w-1.5 cursor-ew-resize touch-none opacity-0 group-hover:bg-black/10 group-hover:opacity-100"
      aria-hidden="true"
      @pointerdown.left.stop.prevent="emit('press', $event, 'left')"
    />

    <div class="break-words text-[13px] font-bold leading-5">{{ card.title }}</div>
    <div
      v-for="(line, i) in card.lines"
      :key="i"
      class="whitespace-pre-line break-words text-xs leading-[1.35]"
      :class="line.style === 'Badge' ? 'mt-0.5' : ''"
    >
      <span v-if="line.label" class="opacity-70">{{ line.label }}{{ /\s$/.test(line.label) ? '' : ' ' }}</span
      ><Badge v-if="line.style === 'Badge'" theme="gray" variant="subtle" size="sm" :label="line.value" /><span v-else :class="lineClass[line.style]">{{ line.value }}</span>
    </div>

    <span
      v-if="canWrite"
      class="absolute inset-y-0 right-0 z-10 w-1.5 cursor-ew-resize touch-none opacity-0 group-hover:bg-black/10 group-hover:opacity-100"
      aria-hidden="true"
      @pointerdown.left.stop.prevent="emit('press', $event, 'right')"
    />
  </div>
</template>
