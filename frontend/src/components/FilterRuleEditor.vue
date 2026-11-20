<script setup lang="ts">
import { Button, Select } from 'frappe-ui'
import { Plus, X } from '@lucide/vue'
import type { FieldDef, ViewFilter } from '@/types'
import FilterValueInput from './FilterValueInput.vue'

const props = defineProps<{ modelValue: ViewFilter[]; fields: FieldDef[]; operators: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: ViewFilter[]): void }>()

const fieldOptions = () => props.fields.map((f) => ({ label: `${f.label} (${f.fieldname})`, value: f.fieldname }))
const operatorOptions = () => props.operators.map((o) => ({ label: o, value: o }))
const def = (name: string) => props.fields.find((f) => f.fieldname === name)

function patch(index: number, change: Partial<ViewFilter>) {
  emit(
    'update:modelValue',
    props.modelValue.map((r, i) => (i === index ? { ...r, ...change } : r)),
  )
}
const add = () => emit('update:modelValue', [...props.modelValue, { field: '', operator: '=', value: '' }])
const remove = (index: number) => emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
</script>

<template>
  <div>
    <p v-if="!modelValue.length" class="mb-2 text-sm text-ink-gray-5">
      No filters: the view shows every record of the source DocType that falls in the visible dates.
    </p>
    <ul class="space-y-2">
      <li v-for="(rule, i) in modelValue" :key="i" class="grid grid-cols-[1.4fr_1fr_1.4fr_auto] items-center gap-2">
        <Select
          :model-value="rule.field"
          :options="[{ label: 'Field…', value: '' }, ...fieldOptions()]"
          @update:model-value="patch(i, { field: $event as string, value: '' })"
        />
        <Select :model-value="rule.operator" :options="operatorOptions()" @update:model-value="patch(i, { operator: $event as string })" />
        <FilterValueInput :model-value="rule.value" :field="def(rule.field)" :operator="rule.operator" @update:model-value="patch(i, { value: $event })" />
        <Button variant="ghost" theme="red" aria-label="Remove filter" @click="remove(i)"><template #icon><X :size="14" /></template></Button>
      </li>
    </ul>
    <Button class="mt-2" variant="solid" theme="gray" label="Add filter" @click="add">
      <template #prefix><Plus :size="14" /></template>
    </Button>
  </div>
</template>
