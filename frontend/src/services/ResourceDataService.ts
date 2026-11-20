import type { CalendarCard, CardUpdate, ResourceData } from '@/types'
import { api, call } from './ERPNextAPIService'
import { toISO } from '@/utils/dates'

/** Rows and cards of a view, and saving a moved/resized card back to the record. */
export const ResourceDataService = {
  load(view: string, start: Date, end: Date) {
    return call<ResourceData>(api('get_resource_data'), { view, start: toISO(start), end: toISO(end) })
  },

  /** Saves the record; the server runs ERPNext's own permission checks and validation. */
  updateCard(view: string, name: string, change: CardUpdate) {
    return call<Pick<CalendarCard, 'name' | 'start' | 'end' | 'resource'>>(api('update_card'), {
      view,
      name,
      ...change,
    })
  },
}
