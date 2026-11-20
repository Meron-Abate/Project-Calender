<script setup lang="ts">
import { computed } from 'vue'
import { Badge, Button } from 'frappe-ui'
import { CalendarDays, ExternalLink, Rows3, X } from '@lucide/vue'
import type { CalendarCard, FieldStyle } from '@/types'
import { cardColor } from '@/utils/colors'
import { datePart, fromISO } from '@/utils/dates'

const props = defineProps<{
  card: CalendarCard
  /** Label of the row (resource) the card sits in. */
  rowLabel: string
  resourceLabel: string
  doctype: string
  /** URL of the record in Desk (the "detail DocType"). */
  recordUrl: string
  /** Admins (System Manager) choose the detail fields; everyone else is pointed to one. */
  isAdmin: boolean
}>()
defineEmits<{
  (e: 'close'): void
  (e: 'edit-view'): void
}>()

const color = computed(() => cardColor(props.card.color))

const fmt = new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' })
const when = computed(() => {
  const a = datePart(props.card.start)
  const b = datePart(props.card.end)
  const start = fmt.format(fromISO(a))
  return a === b ? start : `${start} – ${fmt.format(fromISO(b))}`
})

const valueClass: Record<FieldStyle, string> = {
  Normal: 'text-ink-gray-9',
  Bold: 'font-semibold text-ink-gray-9',
  Muted: 'text-ink-gray-6',
  Italic: 'italic text-ink-gray-9',
  Badge: '',
}
</script>

<template>
  <aside class="flex h-full w-[22rem] shrink-0 flex-col border-l border-outline-gray-2 bg-surface-white shadow-xl" aria-label="Details">
    <header class="flex items-start gap-3 border-b border-outline-gray-1 px-5 py-4">
      <span class="mt-1.5 h-3 w-3 shrink-0 rounded-full" :style="{ backgroundColor: color.accent }" />
      <div class="min-w-0 flex-1">
        <h2 class="break-words text-lg font-semibold leading-6 text-ink-gray-9">{{ card.title }}</h2>
        <p class="mt-0.5 text-sm text-ink-gray-6">{{ doctype }} · {{ card.name }}</p>
      </div>
      <Button variant="ghost" aria-label="Close" @click="$emit('close')">
        <template #icon><X :size="16" /></template>
      </Button>
    </header>

    <div class="flex-1 space-y-5 overflow-y-auto px-5 py-4">
      <dl class="space-y-3 text-sm">
        <div class="flex items-start gap-3">
          <CalendarDays :size="16" class="mt-0.5 shrink-0 text-ink-gray-5" />
          <dt class="w-24 shrink-0 text-ink-gray-6">Dates</dt>
          <dd class="text-ink-gray-9">{{ when }}</dd>
        </div>
        <div v-if="resourceLabel" class="flex items-start gap-3">
          <Rows3 :size="16" class="mt-0.5 shrink-0 text-ink-gray-5" />
          <dt class="w-24 shrink-0 text-ink-gray-6">{{ resourceLabel }}</dt>
          <dd class="text-ink-gray-9">{{ rowLabel }}</dd>
        </div>
      </dl>

      <div class="border-t border-outline-gray-1 pt-4">
        <div v-if="!card.details.length" class="rounded-lg bg-surface-gray-1 px-4 py-5 text-center">
          <template v-if="isAdmin">
            <p class="text-sm font-medium text-ink-gray-8">Select detail fields to come here</p>
            <p class="mt-1 text-sm text-ink-gray-6">
              Tick <span class="font-medium">Show in detail</span> on a card body field of this view and its value will
              appear in this panel.
            </p>
            <button type="button" class="mt-3 text-sm text-ink-blue-3 hover:underline" @click="$emit('edit-view')">
              Edit this view's fields
            </button>
          </template>
          <template v-else>
            <p class="text-sm font-medium text-ink-gray-8">No details to show yet</p>
            <p class="mt-1 text-sm text-ink-gray-6">Talk to your admin to choose which fields appear here.</p>
          </template>
        </div>
        <dl v-else class="space-y-3 text-sm">
          <div v-for="(line, i) in card.details" :key="i">
            <dt class="text-xs text-ink-gray-5">{{ line.label }}</dt>
            <dd class="mt-0.5 whitespace-pre-line break-words" :class="valueClass[line.style]">
              <Badge v-if="line.style === 'Badge'" theme="gray" variant="subtle" :label="line.value" />
              <template v-else>{{ line.value }}</template>
            </dd>
          </div>
        </dl>
      </div>
    </div>

    <footer class="border-t border-outline-gray-1 p-4">
      <Button class="w-full" variant="solid" theme="gray" :label="`Open ${doctype} in Desk`" :link="recordUrl">
        <template #prefix><ExternalLink :size="14" /></template>
      </Button>
    </footer>
  </aside>
</template>
