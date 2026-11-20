<script setup lang="ts">
import { computed } from 'vue'
import { Sidebar, SidebarItem } from 'frappe-ui'
import { Check, LogOut, Settings2 } from '@lucide/vue'
import type { ResourceView } from '@/types'

const props = defineProps<{
  views: ResourceView[]
  /** `name` of the view being shown. */
  currentName: string | null
}>()
const emit = defineEmits<{
  (e: 'select', name: string): void
  (e: 'manage'): void
}>()

const current = computed(() => props.views.find((v) => v.name === props.currentName) ?? null)

// The header is frappe-ui's own sidebar dropdown: every saved view, then Manage Views.
const header = computed(() => ({
  title: current.value?.view_name ?? 'No view',
  subtitle: current.value?.source_doctype ?? 'Resource calendar',
  menuItems: [
    {
      group: 'Views',
      items: props.views.length
        ? props.views.map((v) => ({
            label: v.view_name,
            icon: v.name === props.currentName ? Check : null,
            onClick: () => emit('select', v.name!),
          }))
        : [{ label: 'No saved views yet', disabled: true }],
    },
    { group: '', items: [{ label: 'Manage Views', icon: Settings2, onClick: () => emit('manage') }] },
  ],
}))

const toDesk = () => (window.location.href = '/desk')
</script>

<template>
  <!-- no filters here: the view's own filters decide what shows -->
  <Sidebar :header="(header as any)">
    <template #footer-items="{ isCollapsed }">
      <SidebarItem label="Exit to Desk" :icon="LogOut" :is-collapsed="isCollapsed" :on-click="toDesk" />
    </template>
  </Sidebar>
</template>
