export type Timeframe = 'week' | '2weeks' | 'month'

export type FieldStyle = 'Normal' | 'Bold' | 'Muted' | 'Italic' | 'Badge'

export interface ViewFilter {
  field: string
  operator: string
  value: string
}

export interface ViewField {
  field: string
  /** Optional prefix shown before the value, e.g. "Client:". */
  label: string
  style: FieldStyle
  /** Also list this field in the right-hand detail panel when a card is clicked. */
  show_in_detail: 0 | 1
}

/** A saved Resource View: configuration only. The cards are the source DocType's real records. */
export interface ResourceView {
  name?: string
  view_name: string
  source_doctype: string
  /** Optional: empty means every card sits in one row. */
  resource_field: string
  show_empty_resources: 0 | 1
  card_title_field: string
  start_field: string
  end_field: string
  color_field: string
  sort_order: number
  filters: ViewFilter[]
  fields: ViewField[]
}

export interface ViewList {
  views: ResourceView[]
  can_write: boolean
  can_create: boolean
  /** System Manager: may change which fields the detail panel shows. */
  is_admin: boolean
}

export interface FieldDef {
  fieldname: string
  label: string
  fieldtype: string
  options: string | null
  /** Options of a Select field. */
  choices: string[]
}

export interface DocTypeFields {
  doctype: string
  fields: FieldDef[]
  operators: string[]
  styles: FieldStyle[]
  resource_types: string[]
  title_types: string[]
  date_types: string[]
  color_types: string[]
}

export interface DocTypeOption {
  name: string
  module: string | null
}

export interface ResourceRow {
  value: string
  label: string
}

export interface CardLine {
  label: string
  value: string
  style: FieldStyle
}

export interface CalendarCard {
  name: string
  /** Value of the resource field; '' means unassigned. */
  resource: string
  title: string
  /** 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS', exactly as stored. */
  start: string
  end: string
  color: string
  lines: CardLine[]
  /** The body fields marked "Show in detail", for the side panel. */
  details: CardLine[]
}

export interface ResourceData {
  view: ResourceView
  rows: ResourceRow[]
  cards: CalendarCard[]
  truncated: boolean
  meta: {
    start_type: string
    end_type: string
    resource_label: string
    can_create: boolean
    can_write: boolean
  }
}

export interface CardUpdate {
  start?: string
  end?: string
  resource?: string
}

export interface AppEntry {
  name: string
  title: string
  logo?: string
  route: string
}
