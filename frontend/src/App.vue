<script setup lang="ts">
import { Dialogs, FrappeUIProvider } from 'frappe-ui'
import ResourceCalendar from '@/components/ResourceCalendar.vue'
</script>

<template>
  <!-- the provider hosts frappe-ui's toasts; Dialogs hosts its confirm dialogs -->
  <FrappeUIProvider>
    <ResourceCalendar />
    <Dialogs />
  </FrappeUIProvider>
</template>
