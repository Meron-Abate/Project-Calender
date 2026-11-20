<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import type { CalendarCard, CardUpdate, ResourceRow } from '@/types'
import { dayLabel, diffDays, isSameDay, isWeekend, shiftStamp, today, toISO, weekday } from '@/utils/dates'
import { layoutVisible, type PlacedItem } from '@/utils/layout'
import ResourceCard from './ResourceCard.vue'

const LABEL_WIDTH = 220 // sticky resource column
const DAY_WIDTH = 136 // minimum width of one day column

const props = defineProps<{
  rows: ResourceRow[]
  cards: CalendarCard[]
  /** The visible days (weekends already removed when they are hidden). */
  days: Date[]
  resourceLabel: string
  canWrite: boolean
}>()
const emit = defineEmits<{
  (e: 'open', card: CalendarCard): void
  (e: 'update', card: CalendarCard, change: CardUpdate): void
}>()

const now = today()
const columns = computed(() => `repeat(${props.days.length}, minmax(0, 1fr))`)
const minWidth = computed(() => `${LABEL_WIDTH + props.days.length * DAY_WIDTH}px`)

// One layout per row: overlapping cards get their own lane and the row grows to fit them.
const layouts = computed(() => {
  const byRow = new Map<string, CalendarCard[]>()
  for (const card of props.cards) {
    const list = byRow.get(card.resource) ?? []
    list.push(card)
    byRow.set(card.resource, list)
  }
  const out = new Map<string, ReturnType<typeof layoutVisible<CalendarCard>>>()
  for (const row of props.rows) out.set(row.value, layoutVisible(byRow.get(row.value) ?? [], props.days))
  return out
})

// --- drag to move, drag the edges to resize --------------------------------------------------------
type Mode = 'move' | 'left' | 'right'
interface Drag {
  placed: PlacedItem<CalendarCard>
  mode: Mode
  startX: number
  startY: number
  dayWidth: number
  dx: number
  dy: number
  /** Whole visible-day columns moved (move/left) or added to the width (right). */
  delta: number
  row: string
  moved: boolean
}
const drag = ref<Drag | null>(null)
const THRESHOLD = 4

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi)

function press(event: PointerEvent, placed: PlacedItem<CalendarCard>, mode: Mode) {
  const area = (event.currentTarget as HTMLElement).closest('[data-cards]') as HTMLElement | null
  if (!area) return
  drag.value = {
    placed,
    mode: props.canWrite ? mode : 'move',
    startX: event.clientX,
    startY: event.clientY,
    dayWidth: area.getBoundingClientRect().width / props.days.length,
    dx: 0,
    dy: 0,
    delta: 0,
    row: placed.item.resource,
    moved: false,
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
  window.addEventListener('pointercancel', cancel)
}

function rowUnderPointer(x: number, y: number): string | null {
  for (const el of document.elementsFromPoint(x, y)) {
    const value = (el as HTMLElement).dataset?.rowValue
    if (value !== undefined) return value
  }
  return null
}

function onMove(event: PointerEvent) {
  const d = drag.value
  if (!d || !props.canWrite) return
  const dx = event.clientX - d.startX
  const dy = event.clientY - d.startY
  if (!d.moved && Math.hypot(dx, dy) < THRESHOLD) return
  d.moved = true

  const { col, span } = d.placed
  const total = props.days.length
  const raw = Math.round(dx / d.dayWidth)
  if (d.mode === 'move') {
    d.delta = clamp(col + raw, 0, total - span) - col
    d.row = rowUnderPointer(event.clientX, event.clientY) ?? d.row
  } else if (d.mode === 'right') {
    d.delta = clamp(span + raw, 1, total - col) - span
  } else {
    d.delta = clamp(col + raw, 0, col + span - 1) - col
  }
  d.dx = d.mode === 'move' ? d.delta * d.dayWidth : dx
  d.dy = d.mode === 'move' ? dy : 0
}

function cleanup() {
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
  window.removeEventListener('pointercancel', cancel)
}
function cancel() {
  cleanup()
  drag.value = null
}

function onUp() {
  const d = drag.value
  cleanup()
  drag.value = null
  if (!d) return
  const card = d.placed.item
  if (!d.moved) return emit('open', card)

  const { col, span } = d.placed
  const day = (i: number) => props.days[i]
  const change: CardUpdate = {}
  if (d.mode === 'move') {
    if (d.delta) {
      const shift = diffDays(day(col), day(col + d.delta))
      change.start = shiftStamp(card.start, shift)
      change.end = shiftStamp(card.end, shift)
    }
    if (d.row !== card.resource) change.resource = d.row
  } else if (d.mode === 'right' && d.delta) {
    change.end = shiftStamp(card.end, diffDays(day(col + span - 1), day(col + span - 1 + d.delta)))
  } else if (d.mode === 'left' && d.delta) {
    change.start = shiftStamp(card.start, diffDays(day(col), day(col + d.delta)))
  }
  if (Object.keys(change).length) emit('update', card, change)
}

onBeforeUnmount(cleanup)

/** Where a card sits right now, including a live resize preview. */
function geometry(p: PlacedItem<CalendarCard>) {
  const d = drag.value
  if (d && d.moved && d.placed.item.name === p.item.name) {
    if (d.mode === 'right') return { col: p.col, span: p.span + d.delta }
    if (d.mode === 'left') return { col: p.col + d.delta, span: p.span - d.delta }
  }
  return { col: p.col, span: p.span }
}
const isDragging = (p: PlacedItem<CalendarCard>) =>
  !!drag.value?.moved && drag.value.mode === 'move' && drag.value.placed.item.name === p.item.name
const isDropRow = (value: string) => !!drag.value?.moved && drag.value.mode === 'move' && drag.value.row === value
</script>

<template>
  <div class="flex-1 overflow-auto bg-surface-white" :class="drag?.moved ? 'select-none' : ''">
    <div :style="{ minWidth }">
      <!-- day header -->
      <div class="sticky top-0 z-20 flex border-b border-outline-gray-2 bg-surface-white">
        <div
          class="sticky left-0 z-30 flex shrink-0 items-end border-r border-outline-gray-2 bg-surface-white px-3 py-2 text-xs font-medium uppercase tracking-wide text-ink-gray-5"
          :style="{ width: `${LABEL_WIDTH}px` }"
        >
          {{ resourceLabel }}
        </div>
        <div class="grid flex-1" :style="{ gridTemplateColumns: columns }">
          <div
            v-for="d in days"
            :key="toISO(d)"
            class="border-r border-outline-gray-1 px-2 py-2 text-center last:border-r-0"
            :class="isWeekend(d) ? 'bg-surface-gray-1' : ''"
          >
            <div class="text-sm font-medium" :class="isWeekend(d) ? 'text-ink-gray-5' : 'text-ink-gray-8'">{{ weekday(d) }}</div>
            <div
              class="mx-auto mt-0.5 inline-block rounded-full px-2 text-xs"
              :class="isSameDay(d, now) ? 'bg-surface-blue-3 font-medium text-white' : 'text-ink-gray-6'"
            >
              {{ dayLabel(d) }}
            </div>
          </div>
        </div>
      </div>

      <p v-if="!rows.length" class="px-6 py-16 text-center text-sm text-ink-gray-5">
        Nothing is scheduled in this range.
      </p>

      <!-- one row per resource -->
      <div
        v-for="row in rows"
        :key="row.value"
        :data-row-value="row.value"
        class="flex border-b border-outline-gray-1"
        :class="isDropRow(row.value) ? 'bg-surface-blue-1' : ''"
      >
        <div
          class="sticky left-0 z-10 shrink-0 border-r border-outline-gray-2 px-3 py-3 text-sm font-medium"
          :class="[isDropRow(row.value) ? 'bg-surface-blue-1' : 'bg-surface-white', row.label === 'Unassigned' ? 'italic text-ink-gray-5' : 'text-ink-gray-9']"
          :style="{ width: `${LABEL_WIDTH}px` }"
        >
          <span class="break-words">{{ row.label }}</span>
        </div>

        <div class="relative min-h-[72px] flex-1" data-cards>
          <!-- day column backgrounds -->
          <div class="pointer-events-none absolute inset-0 grid" :style="{ gridTemplateColumns: columns }" aria-hidden="true">
            <div
              v-for="d in days"
              :key="toISO(d)"
              class="border-r border-outline-gray-1 last:border-r-0"
              :class="isSameDay(d, now) ? 'bg-surface-blue-1/50' : isWeekend(d) ? 'bg-surface-gray-1' : ''"
            />
          </div>

          <!-- cards: each lane is its own grid row, so rows grow with their content and overlaps stack -->
          <div
            class="relative grid items-stretch gap-y-1.5 px-0 py-1.5"
            :style="{ gridTemplateColumns: columns, gridAutoRows: 'auto' }"
          >
            <div
              v-for="p in layouts.get(row.value)?.placed ?? []"
              :key="p.item.name"
              class="min-w-0 px-[3px]"
              :class="isDragging(p) ? 'z-30' : ''"
              :style="{
                gridColumn: `${geometry(p).col + 1} / span ${Math.max(1, geometry(p).span)}`,
                gridRow: `${p.lane + 1}`,
              }"
            >
              <ResourceCard
                :card="p.item"
                :can-write="canWrite"
                :dragging="isDragging(p)"
                :offset-x="drag?.dx"
                :offset-y="drag?.dy"
                :continues-before="p.continuesBefore"
                :continues-after="p.continuesAfter"
                @press="(e, mode) => press(e, p, mode)"
                @open="emit('open', p.item)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
