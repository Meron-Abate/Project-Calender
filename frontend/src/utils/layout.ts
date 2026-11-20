import { datePart, toISO } from './dates'

export interface Spanning {
  /** 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'. */
  start: string
  /** Inclusive end, same format. */
  end: string
}

export interface PlacedItem<T> {
  item: T
  /** 0-based index of the first visible day the item covers. */
  col: number
  /** Number of visible day columns it covers. */
  span: number
  /** 0-based lane. Items that overlap in time never share a lane, so none can hide another. */
  lane: number
  continuesBefore: boolean
  continuesAfter: boolean
}

export interface RowLayout<T> {
  placed: PlacedItem<T>[]
  lanes: number
}

/**
 * Packs items into lanes over the visible days.
 *
 * `days` may skip some calendar days (hidden weekends). An item covers every visible day between its
 * start and end; one that falls only on hidden days is left out. Items are sorted by start and then by
 * length and each takes the first lane that is already free.
 */
export function layoutVisible<T extends Spanning>(items: T[], days: Date[]): RowLayout<T> {
  const keys = days.map(toISO)
  const first = keys[0]
  const last = keys[keys.length - 1]

  const candidates: { item: T; from: string; to: string; col: number; lastCol: number }[] = []
  for (const item of items) {
    const from = datePart(item.start)
    const to = datePart(item.end) < from ? from : datePart(item.end)
    const col = keys.findIndex((k) => k >= from)
    let lastCol = -1
    for (let i = keys.length - 1; i >= 0; i--) {
      if (keys[i] <= to) {
        lastCol = i
        break
      }
    }
    if (col === -1 || lastCol < col) continue
    candidates.push({ item, from, to, col, lastCol })
  }

  candidates.sort((a, b) => a.col - b.col || b.lastCol - a.lastCol || a.item.start.localeCompare(b.item.start))

  const laneEnds: number[] = []
  const placed: PlacedItem<T>[] = []
  for (const c of candidates) {
    let lane = laneEnds.findIndex((end) => end < c.col)
    if (lane === -1) {
      lane = laneEnds.length
      laneEnds.push(c.lastCol)
    } else {
      laneEnds[lane] = c.lastCol
    }
    placed.push({
      item: c.item,
      col: c.col,
      span: c.lastCol - c.col + 1,
      lane,
      continuesBefore: c.from < first,
      continuesAfter: c.to > last,
    })
  }
  return { placed, lanes: laneEnds.length }
}
