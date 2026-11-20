export interface CardColor {
  /** Card fill. */
  bg: string
  /** Left accent bar. */
  accent: string
  /** Text colour. */
  text: string
}

const PALETTE: CardColor[] = [
  { bg: '#D7F2DD', accent: '#22A55B', text: '#14532D' }, // green
  { bg: '#FDEBA8', accent: '#E5A00D', text: '#713F12' }, // yellow
  { bg: '#C7DDFB', accent: '#2F6FDE', text: '#1E3A8A' }, // blue
  { bg: '#E6D5FA', accent: '#9A4DE0', text: '#581C87' }, // purple
  { bg: '#FED8BC', accent: '#EF7B1D', text: '#7C2D12' }, // orange
  { bg: '#BDEFE8', accent: '#0F9D8F', text: '#115E59' }, // teal
  { bg: '#FBCFE0', accent: '#E0457F', text: '#831843' }, // pink
  { bg: '#D6E3A0', accent: '#7C9A12', text: '#3F6212' }, // lime
  { bg: '#C9CFFA', accent: '#5B5BE0', text: '#312E81' }, // indigo
  { bg: '#FBC9C4', accent: '#DC3F3F', text: '#7F1D1D' }, // red
  { bg: '#BDE7F5', accent: '#0E8FC0', text: '#0C4A6E' }, // sky
  { bg: '#E8D8C4', accent: '#A0683A', text: '#5C3A1E' }, // brown
]

const DEFAULT_COLOR = PALETTE[2]
const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i

function hash(text: string): number {
  let h = 5381
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0
  return Math.abs(h)
}

function hexToRgb(hex: string): [number, number, number] {
  const full = hex.length === 4 ? '#' + [...hex.slice(1)].map((c) => c + c).join('') : hex
  return [1, 3, 5].map((i) => parseInt(full.slice(i, i + 2), 16)) as [number, number, number]
}

/**
 * Colour of a card from the view's colour field. A Color field's hex value is used as is; any other value
 * (a Select option, a link name) maps to a fixed palette entry, so the same value always looks the same.
 */
export function cardColor(value: string): CardColor {
  const v = (value ?? '').trim()
  if (!v) return DEFAULT_COLOR
  if (HEX.test(v)) {
    const [r, g, b] = hexToRgb(v)
    return { bg: `rgba(${r}, ${g}, ${b}, 0.18)`, accent: v, text: '#1F2937' }
  }
  return PALETTE[hash(v.toLowerCase()) % PALETTE.length]
}
