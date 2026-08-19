// Validated categorical palette (fixed order — CVD-safe on the adjacent
// pairlist that applies to bar/line/pie charts). Never cycle or reassign by
// rank; a category always gets the slot at its position in a sorted list.
export const CATEGORICAL_PALETTE = [
  '#2a78d6', // blue
  '#eb6834', // orange
  '#1baf7a', // aqua
  '#eda100', // yellow
  '#e87ba4', // magenta
  '#008300', // green
  '#4a3aa7', // violet
  '#e34948', // red
]

// Reserved status colors — used only for genuine polarity (income = inflow,
// expense = outflow), never as an arbitrary series color.
export const STATUS_GOOD = '#0ca30c'
export const STATUS_CRITICAL = '#d03b3b'

export const CHART_MUTED_INK = '#898781'
export const CHART_GRIDLINE = '#e1e0d9'
