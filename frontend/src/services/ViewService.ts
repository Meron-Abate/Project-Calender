import type { ResourceView, ViewList } from '@/types'
import { api, call } from './ERPNextAPIService'

/** Saved Resource Views: create, edit, duplicate, delete. */
export const ViewService = {
  list() {
    return call<ViewList>(api('list_views'))
  },

  save(view: ResourceView) {
    return call<ResourceView>(api('save_view'), { data: view })
  },

  duplicate(name: string) {
    return call<ResourceView>(api('duplicate_view'), { name })
  },

  remove(name: string) {
    return call<{ name: string }>(api('delete_view'), { name })
  },
}
