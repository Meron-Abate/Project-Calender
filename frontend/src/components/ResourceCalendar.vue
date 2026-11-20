<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { onKeyStroke } from '@vueuse/core'
import { Alert, Button, ErrorMessage, LoadingIndicator, toast } from 'frappe-ui'
import { LayoutGrid } from '@lucide/vue'
import type { CalendarCard, CardUpdate, ResourceData, ResourceView, Timeframe } from '@/types'
import { ViewService } from '@/services/ViewService'
import { ResourceDataService } from '@/services/ResourceDataService'
import { deskUrl } from '@/services/ERPNextAPIService'
import { isWeekend, rangeLabel, spanFor, stepAnchor, today } from '@/utils/dates'
import ViewSidebar from './ViewSidebar.vue'
import TimelineToolbar from './TimelineToolbar.vue'
import ResourceGrid from './ResourceGrid.vue'
import CardDetailPanel from './CardDetailPanel.vue'
import ManageViewsDialog from './ManageViewsDialog.vue'
import ViewEditorDialog from './ViewEditorDialog.vue'

const STORAGE_KEY = 'project_calendar:v2'

// --- remembered per browser (every access is guarded: storage can be blocked) ----------------------
interface Stored {
  view?: string
  timeframe?: Timeframe
  hideWeekends?: boolean
}
function readStored(): Stored {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}')
  } catch {
    return {}
  }
}
function writeStored() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ view: currentName.value, timeframe: timeframe.value, hideWeekends: hideWeekends.value }),
    )
  } catch {
    /* nothing to do */
  }
}

const stored = readStored()
const views = ref<ResourceView[]>([])
const canWrite = ref(false)
const canCreate = ref(false)
const isAdmin = ref(false)
const currentName = ref<string | null>(stored.view ?? null)
const timeframe = ref<Timeframe>(stored.timeframe ?? 'week')
const hideWeekends = ref(stored.hideWeekends ?? false)
const anchor = ref<Date>(today())

const data = ref<ResourceData | null>(null)
const loading = ref(false)
const error = ref('')

const current = computed(() => views.value.find((v) => v.name === currentName.value) ?? null)
const span = computed(() => spanFor(timeframe.value, anchor.value))
const rangeText = computed(() => rangeLabel(timeframe.value, span.value))
const visibleDays = computed(() => (hideWeekends.value ? span.value.days.filter((d) => !isWeekend(d)) : span.value.days))

// --- views ------------------------------------------------------------------------------------------
async function loadViews(select?: string) {
  try {
    const result = await ViewService.list()
    views.value = result.views
    canWrite.value = result.can_write
    canCreate.value = result.can_create
    isAdmin.value = result.is_admin
    const wanted = select ?? currentName.value
    currentName.value = views.value.some((v) => v.name === wanted) ? wanted : (views.value[0]?.name ?? null)
  } catch (e) {
    error.value = (e as Error).message
  }
}

let loadId = 0
async function loadData() {
  const view = current.value
  if (!view) {
    data.value = null
    return
  }
  const id = ++loadId
  loading.value = true
  error.value = ''
  try {
    const result = await ResourceDataService.load(view.name!, span.value.start, span.value.end)
    if (id === loadId) data.value = result
  } catch (e) {
    if (id === loadId) {
      error.value = (e as Error).message
      data.value = null
    }
  } finally {
    if (id === loadId) loading.value = false
  }
}

let debounce: ReturnType<typeof setTimeout> | undefined
watch([currentName, timeframe, anchor], () => {
  writeStored()
  clearTimeout(debounce)
  debounce = setTimeout(loadData, 120)
})
watch(hideWeekends, writeStored)
watch(currentName, () => (selectedName.value = null))

onMounted(async () => {
  await loadViews()
  await loadData()
})

// --- toolbar actions --------------------------------------------------------------------------------
const step = (dir: 1 | -1) => (anchor.value = stepAnchor(timeframe.value, anchor.value, dir))
const goToday = () => (anchor.value = today())

// --- clicking a card --------------------------------------------------------------------------------
// A click opens the side panel: it lists the "Show in detail" fields, or says to pick some.
const selectedName = ref<string | null>(null)
const selectedCard = computed(() => data.value?.cards.find((c) => c.name === selectedName.value) ?? null)
const selectedRowLabel = computed(
  () => data.value?.rows.find((r) => r.value === selectedCard.value?.resource)?.label ?? 'Unassigned',
)

const openCard = (card: CalendarCard) => (selectedName.value = card.name)

/** Drag/resize: show the change at once, save the record, and put the card back if ERPNext refuses. */
async function updateCard(card: CalendarCard, change: CardUpdate) {
  const view = current.value
  const d = data.value
  if (!view || !d) return
  const before = d.cards
  d.cards = before.map((c) =>
    c.name === card.name
      ? {
          ...c,
          ...(change.start !== undefined && { start: change.start }),
          ...(change.end !== undefined && { end: change.end }),
          ...(change.resource !== undefined && { resource: change.resource }),
        }
      : c,
  )
  try {
    await ResourceDataService.updateCard(view.name!, card.name, change)
    toast.success(`${card.title} saved.`)
    await loadData() // pick up server-side formatting, new rows, anything the save changed
  } catch (e) {
    d.cards = before
    toast.error((e as Error).message)
  }
}

// --- managing views ---------------------------------------------------------------------------------
const managerOpen = ref(false)
const editorOpen = ref(false)
const editing = ref<ResourceView | null>(null)
let returnToManager = false

const openManager = () => (managerOpen.value = true)
function createView() {
  editing.value = null
  returnToManager = true
  managerOpen.value = false
  editorOpen.value = true
}
function editView(view: ResourceView) {
  editing.value = view
  returnToManager = true
  managerOpen.value = false
  editorOpen.value = true
}
watch(editorOpen, (isOpen) => {
  if (!isOpen && returnToManager) {
    returnToManager = false
    managerOpen.value = true
  }
})
async function onSaved(view: ResourceView) {
  toast.success(`View “${view.view_name}” saved.`)
  await loadViews(view.name)
  await loadData()
}
async function onViewsChanged(select?: string) {
  await loadViews(select)
  await loadData()
}
const selectView = (name: string) => (currentName.value = name)

onKeyStroke('Escape', () => {
  if (!managerOpen.value && !editorOpen.value && selectedName.value) selectedName.value = null
})
</script>

<template>
  <!-- isolate: keeps the grid's sticky/z-indexed parts under frappe-ui dialogs, which have no z-index of their own -->
  <div class="isolate flex h-full bg-surface-white text-ink-gray-9">
    <ViewSidebar :views="views" :current-name="currentName" @select="selectView" @manage="openManager" />

    <div class="flex min-w-0 flex-1 flex-col">
      <TimelineToolbar
        v-model:timeframe="timeframe"
        v-model:hide-weekends="hideWeekends"
        :range-text="rangeText"
        :loading="loading"
        @prev="step(-1)"
        @next="step(1)"
        @today="goToday"
      />

      <Alert
        v-if="data?.truncated"
        theme="yellow"
        title="Only the first 2,000 records are shown"
        description="Add filters to this view to narrow it down."
      />

      <div class="flex min-h-0 flex-1">
        <div class="flex min-w-0 flex-1 flex-col">
          <!-- no views at all -->
          <div v-if="!views.length && !error" class="flex flex-1 items-center justify-center p-8">
            <div class="max-w-sm text-center">
              <span class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-surface-gray-2 text-ink-gray-6">
                <LayoutGrid :size="22" />
              </span>
              <h2 class="text-lg font-semibold text-ink-gray-8">No views yet</h2>
              <p class="mt-1 text-sm text-ink-gray-6">
                A view puts any DocType's records on a weekly grid, one row per resource. Pick the DocType and its fields to start.
              </p>
              <Button class="mt-4" variant="solid" theme="gray" label="Create a view" :disabled="!canCreate" @click="createView" />
              <p v-if="!canCreate" class="mt-2 text-xs text-ink-gray-5">Ask a Projects Manager or System Manager to create one.</p>
            </div>
          </div>

          <div v-else-if="error" class="flex flex-1 items-center justify-center p-8">
            <div class="max-w-md text-center">
              <ErrorMessage :message="error" />
              <div class="mt-3 flex justify-center gap-2">
                <Button variant="solid" theme="gray" label="Try again" @click="loadData" />
                <Button v-if="canWrite && current" variant="solid" theme="gray" label="Edit view" @click="editView(current)" />
              </div>
            </div>
          </div>

          <ResourceGrid
            v-else-if="data"
            :rows="data.rows"
            :cards="data.cards"
            :days="visibleDays"
            :resource-label="data.meta.resource_label || 'Records'"
            :can-write="data.meta.can_write"
            @open="openCard"
            @update="updateCard"
          />

          <div v-else class="flex flex-1 items-center justify-center gap-2 text-sm text-ink-gray-5">
            <LoadingIndicator class="h-4 w-4" /> Loading…
          </div>
        </div>

        <!-- right-hand detail panel (only for views with a "Show in detail" field) -->
        <div v-if="selectedCard && data && current" class="fixed inset-y-0 right-0 z-30 lg:static lg:z-auto">
          <CardDetailPanel
            :card="selectedCard"
            :row-label="selectedRowLabel"
            :resource-label="data.meta.resource_label"
            :doctype="current.source_doctype"
            :record-url="deskUrl(current.source_doctype, selectedCard.name)"
            :is-admin="isAdmin"
            @close="selectedName = null"
            @edit-view="editView(current)"
          />
        </div>
      </div>
    </div>

    <ManageViewsDialog
      v-model="managerOpen"
      :views="views"
      :can-write="canWrite"
      :can-create="canCreate"
      @create="createView"
      @edit="editView"
      @changed="onViewsChanged"
    />
    <ViewEditorDialog v-model="editorOpen" :view="editing" @saved="onSaved" />
  </div>
</template>
