<script setup lang="ts">
import { Button, LoadingIndicator, Switch, TabButtons } from 'frappe-ui'
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import type { Timeframe } from '@/types'

defineProps<{
  timeframe: Timeframe
  hideWeekends: boolean
  rangeText: string
  loading: boolean
}>()
const emit = defineEmits<{
  (e: 'update:timeframe', value: Timeframe): void
  (e: 'update:hideWeekends', value: boolean): void
  (e: 'prev'): void
  (e: 'next'): void
  (e: 'today'): void
}>()

const frames = [
  { label: 'Week', value: 'week' },
  { label: '2 Weeks', value: '2weeks' },
  { label: 'Month', value: 'month' },
]
</script>

<template>
  <header class="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-outline-gray-1 bg-surface-white px-4 py-2.5">
    <div class="flex items-center gap-1.5">
      <Button variant="solid" theme="gray" aria-label="Previous" @click="emit('prev')">
        <template #icon><ChevronLeft :size="16" /></template>
      </Button>
      <span class="min-w-[9.5rem] text-center text-base font-medium text-ink-gray-8">{{ rangeText }}</span>
      <Button variant="solid" theme="gray" aria-label="Next" @click="emit('next')">
        <template #icon><ChevronRight :size="16" /></template>
      </Button>
      <Button variant="solid" theme="gray" label="Today" @click="emit('today')" />
      <LoadingIndicator v-if="loading" class="ml-1 h-4 w-4 text-ink-gray-5" />
    </div>

    <TabButtons :buttons="frames" :model-value="timeframe" @update:model-value="emit('update:timeframe', $event as Timeframe)" />

    <Switch label="Hide weekends" :model-value="hideWeekends" @update:model-value="emit('update:hideWeekends', $event)" />

  </header>
</template>
