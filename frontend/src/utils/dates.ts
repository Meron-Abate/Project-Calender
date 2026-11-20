import type { Timeframe } from '@/types'

const pad = (n: number) => String(n).padStart(2, '0')

export const toISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

export const fromISO = (s: string) => {
  const [y, m, d] = s.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d)
}

export const today = () => {
  const n = new Date()
  return new Date(n.getFullYear(), n.getMonth(), n.getDate())
}

export const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)

export const diffDays = (a: Date, b: Date) =>
  Math.round(
    (Date.UTC(b.getFullYear(), b.getMonth(), b.getDate()) - Date.UTC(a.getFullYear(), a.getMonth(), a.getDate())) /
      86400000,
  )

/** Monday-based week start. */
export const startOfWeek = (d: Date) => addDays(d, -((d.getDay() + 6) % 7))

export const isSameDay = (a: Date, b: Date) => toISO(a) === toISO(b)
export const isWeekend = (d: Date) => d.getDay() === 0 || d.getDay() === 6

export interface Span {
  start: Date
  end: Date
  /** Every day from start to end. */
  days: Date[]
}

export function spanFor(timeframe: Timeframe, anchor: Date): Span {
  let start: Date
  let end: Date
  if (timeframe === 'month') {
    start = new Date(anchor.getFullYear(), anchor.getMonth(), 1)
    end = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0)
  } else {
    start = startOfWeek(anchor)
    end = addDays(start, timeframe === 'week' ? 6 : 13)
  }
  return { start, end, days: Array.from({ length: diffDays(start, end) + 1 }, (_, i) => addDays(start, i)) }
}

export function stepAnchor(timeframe: Timeframe, anchor: Date, direction: 1 | -1): Date {
  if (timeframe === 'month') return new Date(anchor.getFullYear(), anchor.getMonth() + direction, 1)
  return addDays(anchor, (timeframe === 'week' ? 7 : 14) * direction)
}

const monthShort = new Intl.DateTimeFormat('en', { month: 'short' })
const monthLong = new Intl.DateTimeFormat('en', { month: 'long' })
const weekdayShort = new Intl.DateTimeFormat('en', { weekday: 'short' })

export const weekday = (d: Date) => weekdayShort.format(d)
export const dayLabel = (d: Date) => `${monthShort.format(d)} ${d.getDate()}`

/** "Dec 15 – 21, 2026", "Nov 30 – Dec 6, 2026" or "December 2026". */
export function rangeLabel(timeframe: Timeframe, span: Span): string {
  const { start, end } = span
  if (timeframe === 'month') return `${monthLong.format(start)} ${start.getFullYear()}`
  const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()
  const endPart = sameMonth ? String(end.getDate()) : dayLabel(end)
  const startYear = start.getFullYear() !== end.getFullYear() ? `, ${start.getFullYear()}` : ''
  return `${dayLabel(start)}${startYear} – ${endPart}, ${end.getFullYear()}`
}

/**
 * Moves a stored value ('YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS') by whole days, keeping the time of day.
 */
export function shiftStamp(stamp: string, days: number): string {
  if (!days) return stamp
  return toISO(addDays(fromISO(stamp), days)) + stamp.slice(10)
}

export const datePart = (stamp: string) => stamp.slice(0, 10)
