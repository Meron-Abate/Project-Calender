import type { DocTypeFields, DocTypeOption } from '@/types'
import { api, call, callRaw } from './ERPNextAPIService'

/** Everything about DocTypes comes from ERPNext's own metadata; nothing is hardcoded per DocType. */
export const DocTypeMetadataService = {
  /** Regular DocTypes the user may read. */
  list(txt = '', limit = 40) {
    return call<DocTypeOption[]>(api('list_doctypes'), { txt, limit })
  },

  /** The real fields of a DocType plus the operators/styles the editor offers. */
  getFields(doctype: string) {
    return call<DocTypeFields>(api('get_doctype_fields'), { doctype })
  },

  /** Autocomplete for a Link value (Frappe's own link search, so it respects permissions). */
  async searchLink(doctype: string, txt: string): Promise<string[]> {
    try {
      const body = await callRaw('frappe.desk.search.search_link', { doctype, txt, page_length: 10 })
      return ((body.results ?? body.message ?? []) as { value: string }[]).map((r) => r.value)
    } catch {
      return []
    }
  },
}
