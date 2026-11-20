<script setup lang="ts">
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue'
import { Badge } from 'frappe-ui'
import { ChevronDown } from '@lucide/vue'

defineProps<{
  title: string
  /** Short summary shown when the section is closed (e.g. "2 filters"). */
  summary?: string
  defaultOpen?: boolean
}>()
</script>

<template>
  <Disclosure v-slot="{ open }" :default-open="defaultOpen" as="section" class="overflow-hidden rounded-lg border border-outline-gray-2">
    <!-- the whole bar toggles the section -->
    <DisclosureButton
      class="flex w-full cursor-pointer items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-outline-gray-3"
      :class="open ? 'bg-surface-gray-1' : ''"
    >
      <span class="text-base font-medium text-ink-gray-8">{{ title }}</span>
      <Badge v-if="summary && !open" class="ml-1" theme="gray" variant="subtle" size="sm" :label="summary" />
      <ChevronDown :size="16" class="ml-auto shrink-0 text-ink-gray-5 transition-transform" :class="open ? 'rotate-180' : ''" aria-hidden="true" />
    </DisclosureButton>
    <DisclosurePanel class="border-t border-outline-gray-1 px-4 pb-4 pt-3">
      <slot />
    </DisclosurePanel>
  </Disclosure>
</template>
