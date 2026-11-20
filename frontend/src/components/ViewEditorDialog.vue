<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Button, Checkbox, Dialog, ErrorMessage, FormControl, LoadingIndicator } from 'frappe-ui'
import type { DocTypeFields, DocTypeOption, ResourceView } from '@/types'
import { DocTypeMetadataService } from '@/services/DocTypeMetadataService'
import { ViewService } from '@/services/ViewService'
import CollapsibleSection from './CollapsibleSection.vue'
import DocTypeAutocomplete from './DocTypeAutocomplete.vue'
import FilterRuleEditor from './FilterRuleEditor.vue'
import BodyFieldEditor from './BodyFieldEditor.vue'

const props = defineProps<{
  modelValue: boolean
  /** The view to edit, or null to create one. */
  view: ResourceView | null
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', open: boolean): void
  (e: 'saved', view: ResourceView): void
}>()

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const blank = (): ResourceView => ({
  view_name: '',
  source_doctype: '',
  resource_field: '',
  show_empty_resources: 0,
  card_title_field: '',
  start_field: '',
  end_field: '',
  color_field: '',
  sort_order: 0,
  filters: [],
  fields: [],
})

const draft = ref<ResourceView>(blank())
const meta = ref<DocTypeFields | null>(null)
const loadingFields = ref(false)
const saving = ref(false)
const error = ref('')

const showEmpty = computed({
  get: () => !!draft.value.show_empty_resources,
  set: (v) => (draft.value.show_empty_resources = v ? 1 : 0),
})

async function loadFields(doctype: string, guess = false) {
  loadingFields.value = true
  error.value = ''
  meta.value = null
  try {
    meta.value = await DocTypeMetadataService.getFields(doctype)
    if (guess) applyGuesses(meta.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loadingFields.value = false
  }
}

/** A starting point for a freshly chosen DocType; everything stays editable. */
function applyGuesses(m: DocTypeFields) {
  const of = (types: string[]) => m.fields.filter((f) => types.includes(f.fieldtype))
  const dates = of(m.date_types).filter((f) => !['creation', 'modified'].includes(f.fieldname))
  const startGuess = dates.find((f) => /start|from|begin/.test(f.fieldname)) ?? dates[0]
  const endGuess = dates.find((f) => /end|(^|_)to($|_)|until/.test(f.fieldname) && f !== startGuess) ?? dates.find((f) => f !== startGuess)
  const titleGuess = m.fields.find((f) => /(^|_)(name|title|subject)$/.test(f.fieldname) && m.title_types.includes(f.fieldtype))
  const d = draft.value
  d.card_title_field = titleGuess?.fieldname ?? 'name'
  d.start_field = startGuess?.fieldname ?? ''
  d.end_field = endGuess?.fieldname ?? startGuess?.fieldname ?? ''
}

watch(
  () => [props.modelValue, props.view] as const,
  ([isOpen, view]) => {
    if (!isOpen) return
    error.value = ''
    draft.value = view ? (JSON.parse(JSON.stringify(view)) as ResourceView) : blank()
    // rows saved before "Show in detail" existed have no value for it
    draft.value.fields = draft.value.fields.map((f) => ({ ...f, show_in_detail: f.show_in_detail ? 1 : 0 }))
    meta.value = null
    if (draft.value.source_doctype) loadFields(draft.value.source_doctype)
  },
  { immediate: true },
)

function chooseSource(d: DocTypeOption) {
  if (d.name === draft.value.source_doctype) return
  // Fields belong to the DocType, so a different source starts a fresh mapping.
  draft.value = {
    ...draft.value,
    source_doctype: d.name,
    resource_field: '',
    card_title_field: '',
    start_field: '',
    end_field: '',
    color_field: '',
    filters: [],
    fields: [],
  }
  loadFields(d.name, true)
}

const options = (types: string[] | undefined, blankLabel?: string) => {
  const list = (meta.value?.fields ?? [])
    .filter((f) => !types || types.includes(f.fieldtype))
    .map((f) => ({ label: `${f.label} (${f.fieldname}) · ${f.fieldtype}`, value: f.fieldname }))
  return blankLabel ? [{ label: blankLabel, value: '' }, ...list] : list
}

const valid = computed(() => {
  const d = draft.value
  return (
    !!d.view_name.trim() &&
    !!d.source_doctype &&
    !!d.card_title_field &&
    !!d.start_field &&
    !!d.end_field &&
    d.filters.every((f) => f.field && f.operator && (f.value !== '' || /^is /.test(f.operator))) &&
    d.fields.every((f) => f.field)
  )
})

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`
const detailCount = computed(() => draft.value.fields.filter((f) => f.show_in_detail).length)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const saved = await ViewService.save({ ...draft.value, view_name: draft.value.view_name.trim() })
    emit('saved', saved)
    open.value = false
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Dialog v-model="open" :options="{ title: view ? `Edit view: ${view.view_name}` : 'New view', size: '4xl' }">
    <template #body-content>
      <div class="max-h-[68vh] space-y-3 overflow-y-auto pr-1">
        <!-- name + source -->
        <div class="grid gap-4 pb-1 sm:grid-cols-2">
          <FormControl v-model="draft.view_name" label="View Name *" type="text" placeholder="e.g. Crew bookings" />
          <DocTypeAutocomplete label="Source DocType *" :model-value="draft.source_doctype" @pick="chooseSource" />
        </div>
        <p v-if="view && draft.source_doctype !== view.source_doctype" class="text-xs text-ink-amber-3">
          A different DocType has different fields, so the mapping below was reset.
        </p>

        <p v-if="loadingFields" class="flex items-center gap-2 py-2 text-sm text-ink-gray-5">
          <LoadingIndicator class="h-4 w-4" /> Reading {{ draft.source_doctype }} fields…
        </p>

        <template v-if="meta && !loadingFields">
          <CollapsibleSection title="Resource rows" default-open :summary="draft.resource_field || 'single row'">
            <div class="grid items-end gap-4 sm:grid-cols-2">
              <FormControl
                v-model="draft.resource_field"
                type="select"
                label="Rows: who or what are the cards booked for? (optional)"
                description="Every different value of this field becomes a row. Customer gives one row per customer; Employee gives one row per person. Leave empty to show every card in a single row."
                :options="options(meta.resource_types, 'No rows (single row)')"
              />
              <Checkbox v-model="showEmpty" :disabled="!draft.resource_field" label="Also show rows that have no cards (free / unbooked)" class="pb-1" />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Card & time fields" default-open :summary="draft.card_title_field ? `${draft.card_title_field}, ${draft.start_field} → ${draft.end_field}` : 'not set'">
            <div class="grid gap-4 sm:grid-cols-2">
              <FormControl v-model="draft.card_title_field" type="select" label="Card title *" description="The bold text on each card." :options="options(meta.title_types, 'Pick a field…')" />
              <FormControl v-model="draft.color_field" type="select" label="Color (optional)" description="Cards with the same value share a colour." :options="options(meta.color_types, 'No color')" />
              <FormControl v-model="draft.start_field" type="select" label="Start date/time *" description="Where a card begins on the calendar." :options="options(meta.date_types, 'Pick a field…')" />
              <FormControl v-model="draft.end_field" type="select" label="End date/time *" description="Where a card ends." :options="options(meta.date_types, 'Pick a field…')" />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="View filters" :default-open="draft.filters.length > 0" :summary="plural(draft.filters.length, 'filter')">
            <FilterRuleEditor v-model="draft.filters" :fields="meta.fields" :operators="meta.operators" />
          </CollapsibleSection>

          <CollapsibleSection
            title="Card body fields"
            :default-open="draft.fields.length > 0"
            :summary="plural(draft.fields.length, 'field') + (detailCount ? `, ${detailCount} in detail` : '')"
          >
            <BodyFieldEditor v-model="draft.fields" :fields="meta.fields" :styles="meta.styles" />
          </CollapsibleSection>
        </template>
      </div>

      <ErrorMessage v-if="error" class="mt-3" :message="error" />
    </template>

    <template #actions>
      <div class="flex w-full justify-end gap-2">
        <Button variant="solid" theme="gray" label="Cancel" @click="open = false" />
        <Button variant="solid" theme="gray" :label="view ? 'Save changes' : 'Create view'" :loading="saving" :disabled="!valid || !meta" @click="save" />
      </div>
    </template>
  </Dialog>
</template>
