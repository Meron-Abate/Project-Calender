<script setup lang="ts">
import { computed, ref } from 'vue'
import { Alert, Button, Dialog, ErrorMessage, confirmDialog } from 'frappe-ui'
import { Copy, Pencil, Plus, Trash2 } from '@lucide/vue'
import type { ResourceView } from '@/types'
import { ViewService } from '@/services/ViewService'

const props = defineProps<{
  modelValue: boolean
  views: ResourceView[]
  canWrite: boolean
  canCreate: boolean
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', open: boolean): void
  (e: 'create'): void
  (e: 'edit', view: ResourceView): void
  /** A view was duplicated or deleted; reload the list. */
  (e: 'changed', selectName?: string): void
}>()

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const busy = ref<string | null>(null)
const error = ref('')

async function duplicate(view: ResourceView) {
  busy.value = view.name ?? null
  error.value = ''
  try {
    const copy = await ViewService.duplicate(view.name!)
    emit('changed', copy.name)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = null
  }
}

const escapeHtml = (text: string) =>
  text.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)

function remove(view: ResourceView) {
  confirmDialog({
    title: 'Delete view',
    message: `Delete the view <b>${escapeHtml(view.view_name)}</b>? Your ${escapeHtml(view.source_doctype)} records are not touched.`,
    onConfirm: async ({ hideDialog }: { hideDialog: () => void }) => {
      busy.value = view.name ?? null
      error.value = ''
      try {
        await ViewService.remove(view.name!)
        hideDialog()
        emit('changed')
      } catch (e) {
        hideDialog()
        error.value = (e as Error).message
      } finally {
        busy.value = null
      }
    },
  })
}

const summary = (v: ResourceView) =>
  `${v.source_doctype} · rows: ${v.resource_field || 'single row'} · ${v.start_field} → ${v.end_field}` +
  (v.filters.length ? ` · ${v.filters.length} filter${v.filters.length === 1 ? '' : 's'}` : '')
</script>

<template>
  <Dialog v-model="open" :options="{ title: 'Manage Views', size: '3xl' }">
    <template #body-content>
      <div class="mb-3 flex items-center justify-between gap-3">
        <p class="text-sm text-ink-gray-6">Each view shows one DocType's records on the weekly grid.</p>
        <Button variant="solid" theme="gray" label="New view" :disabled="!canCreate" @click="emit('create')">
          <template #prefix><Plus :size="14" /></template>
        </Button>
      </div>

      <ErrorMessage v-if="error" class="mb-3" :message="error" />
      <Alert
        v-if="!canWrite"
        class="mb-3"
        theme="blue"
        title="You can open views but can't change them"
        description="Changing views needs the Projects Manager or System Manager role."
      />

      <p v-if="!views.length" class="rounded-lg bg-surface-gray-1 px-3 py-8 text-center text-sm text-ink-gray-6">
        No views yet. Create one to see a DocType's records on the calendar.
      </p>
      <ul v-else class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2">
        <li v-for="v in views" :key="v.name" class="flex items-center gap-3 px-4 py-3">
          <div class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-ink-gray-9">{{ v.view_name }}</div>
            <div class="truncate text-xs text-ink-gray-5">{{ summary(v) }}</div>
          </div>
          <Button variant="solid" theme="gray" :disabled="!canWrite || busy === v.name" label="Edit" @click="emit('edit', v)">
            <template #prefix><Pencil :size="14" /></template>
          </Button>
          <Button variant="solid" theme="gray" :disabled="!canCreate || busy === v.name" :loading="busy === v.name" label="Duplicate" @click="duplicate(v)">
            <template #prefix><Copy :size="14" /></template>
          </Button>
          <Button variant="solid" theme="gray" :disabled="!canWrite || busy === v.name" label="Delete" @click="remove(v)">
            <template #prefix><Trash2 :size="14" /></template>
          </Button>
        </li>
      </ul>
    </template>

    <template #actions>
      <div class="flex w-full justify-end">
        <Button variant="solid" theme="gray" label="Close" @click="open = false" />
      </div>
    </template>
  </Dialog>
</template>
