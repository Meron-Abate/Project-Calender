<script setup lang="ts">
import { Button, Checkbox, Select, TextInput } from 'frappe-ui'
import { ArrowDown, ArrowUp, Plus, X } from '@lucide/vue'
import type { FieldDef, FieldStyle, ViewField } from '@/types'

const props = defineProps<{ modelValue: ViewField[]; fields: FieldDef[]; styles: FieldStyle[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: ViewField[]): void }>()

const fieldOptions = () => props.fields.map((f) => ({ label: `${f.label} (${f.fieldname})`, value: f.fieldname }))
const styleOptions = () => props.styles.map((s) => ({ label: s, value: s }))

function patch(index: number, change: Partial<ViewField>) {
  emit(
    'update:modelValue',
    props.modelValue.map((r, i) => (i === index ? { ...r, ...change } : r)),
  )
}
function move(index: number, by: -1 | 1) {
  const target = index + by
  if (target < 0 || target >= props.modelValue.length) return
  const next = [...props.modelValue]
  ;[next[index], next[target]] = [next[target], next[index]]
  emit('update:modelValue', next)
}
const add = () => emit('update:modelValue', [...props.modelValue, { field: '', label: '', style: 'Normal', show_in_detail: 0 }])
const remove = (index: number) => emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
</script>

<template>
  <div>
    <p v-if="!modelValue.length" class="mb-2 text-sm text-ink-gray-5">
      Cards show only the title. Add fields to list more lines under it, in this order. Tick “Show in detail” to also
      list a field in the side panel that opens when a card is clicked.
    </p>
    <ul class="space-y-2">
      <li v-for="(row, i) in modelValue" :key="i" class="grid grid-cols-[1.5fr_1fr_0.8fr_auto_auto] items-center gap-2">
        <Select
          :model-value="row.field"
          :options="[{ label: 'Field…', value: '' }, ...fieldOptions()]"
          @update:model-value="patch(i, { field: $event as string })"
        />
        <TextInput type="text" placeholder="Prefix label (optional)" :model-value="row.label" @update:model-value="patch(i, { label: $event as string })" />
        <Select :model-value="row.style" :options="styleOptions()" @update:model-value="patch(i, { style: $event as FieldStyle })" />
        <Checkbox label="Show in detail" :model-value="!!row.show_in_detail" @update:model-value="patch(i, { show_in_detail: $event ? 1 : 0 })" />
        <div class="flex items-center">
          <Button variant="ghost" aria-label="Move up" :disabled="i === 0" @click="move(i, -1)"><template #icon><ArrowUp :size="14" /></template></Button>
          <Button variant="ghost" aria-label="Move down" :disabled="i === modelValue.length - 1" @click="move(i, 1)"><template #icon><ArrowDown :size="14" /></template></Button>
          <Button variant="ghost" theme="red" aria-label="Remove field" @click="remove(i)"><template #icon><X :size="14" /></template></Button>
        </div>
      </li>
    </ul>
    <Button class="mt-2" variant="solid" theme="gray" label="Add Field" @click="add">
      <template #prefix><Plus :size="14" /></template>
    </Button>
  </div>
</template>
