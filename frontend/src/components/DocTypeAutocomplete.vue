<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { LoadingIndicator, TextInput } from 'frappe-ui'
import { Check } from '@lucide/vue'
import type { DocTypeOption } from '@/types'
import { DocTypeMetadataService } from '@/services/DocTypeMetadataService'

// Not frappe-ui's Autocomplete: its list is rendered in a portal outside the modal Dialog, where the
// dialog blocks clicks. This list stays inside the dialog, so every option is clickable.
const props = defineProps<{ modelValue: string; label?: string; placeholder?: string }>()
const emit = defineEmits<{ (e: 'pick', doctype: DocTypeOption): void }>()

const items = ref<DocTypeOption[]>([])
const loading = ref(false)
const open = ref(false)
const query = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
let latest = 0

async function search(txt: string) {
  const id = ++latest
  loading.value = true
  try {
    const result = await DocTypeMetadataService.list(txt.trim())
    if (id === latest) items.value = result
  } catch {
    if (id === latest) items.value = []
  } finally {
    if (id === latest) loading.value = false
  }
}

function onType(txt: string) {
  query.value = txt
  open.value = true
  clearTimeout(timer)
  timer = setTimeout(() => search(txt), 250)
}
function onFocus() {
  query.value = ''
  open.value = true
  search('')
}
function pick(d: DocTypeOption) {
  open.value = false
  query.value = ''
  emit('pick', d)
}

// the box shows the chosen DocType until you start searching
const shown = computed(() => (open.value ? query.value : props.modelValue))
onMounted(() => search(''))
</script>

<template>
  <div>
    <label v-if="label" class="mb-1.5 block text-xs text-ink-gray-5">{{ label }}</label>
    <TextInput
      type="text"
      :model-value="shown"
      :placeholder="open && modelValue ? modelValue : (placeholder ?? 'Search DocTypes…')"
      @update:model-value="onType($event as string)"
      @focus="onFocus"
      @blur="open = false"
      @keydown.esc.stop="open = false"
    />

    <!-- in the page flow on purpose (not floating), so the dialog's own scroll area never clips it -->
    <ul v-if="open" class="mt-1 max-h-56 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white p-1 shadow-sm" role="listbox">
      <li v-if="loading" class="flex items-center gap-2 px-2.5 py-2 text-sm text-ink-gray-5">
        <LoadingIndicator class="h-3.5 w-3.5" /> Searching…
      </li>
      <li v-else-if="!items.length" class="px-2.5 py-2 text-sm text-ink-gray-5">No DocTypes found.</li>
      <li v-for="d in items" :key="d.name" role="option" :aria-selected="d.name === modelValue">
        <!-- mousedown (not click) so the input's blur doesn't close the list before the pick lands -->
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded px-2.5 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
          @mousedown.prevent="pick(d)"
        >
          <span class="truncate">{{ d.name }}</span>
          <Check v-if="d.name === modelValue" :size="14" class="shrink-0 text-ink-gray-6" />
          <span v-if="d.module" class="ml-auto shrink-0 text-xs text-ink-gray-5">{{ d.module }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>
