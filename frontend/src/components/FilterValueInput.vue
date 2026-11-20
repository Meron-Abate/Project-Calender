<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Select, TextInput } from 'frappe-ui'
import type { FieldDef } from '@/types'
import { DocTypeMetadataService } from '@/services/DocTypeMetadataService'

const props = defineProps<{ modelValue: string; field: FieldDef | undefined; operator: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

const listId = `fv-${Math.random().toString(36).slice(2, 8)}`
const suggestions = ref<string[]>([])
let timer: ReturnType<typeof setTimeout> | undefined

const multi = computed(() => props.operator === 'in' || props.operator === 'not in')
const noValue = computed(() => props.operator === 'is set' || props.operator === 'is not set')
const kind = computed<'none' | 'select' | 'check' | 'date' | 'link' | 'text'>(() => {
  const f = props.field
  if (noValue.value) return 'none'
  if (!f) return 'text'
  if (f.fieldtype === 'Check') return 'check'
  if (f.fieldtype === 'Select' && !multi.value && f.choices.length) return 'select'
  if ((f.fieldtype === 'Date' || f.fieldtype === 'Datetime') && !multi.value && !/like/.test(props.operator)) return 'date'
  if (f.fieldtype === 'Link' && f.options && !multi.value && !/like/.test(props.operator)) return 'link'
  return 'text'
})

function suggest(txt: string) {
  emit('update:modelValue', txt)
  if (kind.value !== 'link' || !props.field?.options) return
  clearTimeout(timer)
  const doctype = props.field.options
  timer = setTimeout(async () => (suggestions.value = await DocTypeMetadataService.searchLink(doctype, txt)), 200)
}
watch(() => props.field?.fieldname, () => (suggestions.value = []))
</script>

<template>
  <span v-if="kind === 'none'" class="px-2 text-sm text-ink-gray-4">—</span>

  <Select
    v-else-if="kind === 'select'"
    :model-value="modelValue"
    :options="[{ label: 'Pick a value', value: '' }, ...(field?.choices ?? []).map((c) => ({ label: c, value: c }))]"
    @update:model-value="emit('update:modelValue', $event as string)"
  />

  <Select
    v-else-if="kind === 'check'"
    :model-value="modelValue"
    :options="[{ label: 'Yes', value: '1' }, { label: 'No', value: '0' }]"
    @update:model-value="emit('update:modelValue', $event as string)"
  />

  <TextInput
    v-else-if="kind === 'date'"
    type="date"
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event as string)"
  />

  <template v-else-if="kind === 'link'">
    <TextInput
      :model-value="modelValue"
      :list="listId"
      type="text"
      :placeholder="`Search ${field?.options}…`"
      @update:model-value="suggest($event as string)"
      @focus="suggest(modelValue)"
    />
    <datalist :id="listId">
      <option v-for="s in suggestions" :key="s" :value="s" />
    </datalist>
  </template>

  <TextInput
    v-else
    type="text"
    :placeholder="multi ? 'value, value, …' : 'Value (or __user, today)'"
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event as string)"
  />
</template>
