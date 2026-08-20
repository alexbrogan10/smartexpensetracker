import { describe, expect, it } from 'vitest'
import { formatCurrency, formatDate, formatDateTime, formatMonthYear } from './format'

describe('formatCurrency', () => {
  it('formats a decimal string as USD', () => {
    expect(formatCurrency('42.50')).toBe('$42.50')
  })

  it('formats a whole-number string with two decimal places', () => {
    expect(formatCurrency('3000')).toBe('$3,000.00')
  })

  it('formats a negative amount', () => {
    expect(formatCurrency('-15.25')).toBe('-$15.25')
  })
})

describe('formatDate', () => {
  it('formats a plain YYYY-MM-DD string without shifting timezone', () => {
    expect(formatDate('2026-08-19')).toBe('Aug 19, 2026')
  })

  it('formats the first of a month correctly', () => {
    expect(formatDate('2026-01-01')).toBe('Jan 1, 2026')
  })
})

describe('formatDateTime', () => {
  it('formats a full ISO timestamp', () => {
    const result = formatDateTime('2026-08-19T16:29:00Z')
    expect(result).toContain('2026')
    expect(result).toContain('Aug')
  })

  it('does not produce "Invalid Date" for a timestamp with an offset', () => {
    expect(formatDateTime('2026-08-19T16:29:00+00:00')).not.toContain('Invalid')
  })
})

describe('formatMonthYear', () => {
  it('formats a month/year pair as a full month name', () => {
    expect(formatMonthYear(8, 2026)).toBe('August 2026')
  })

  it('handles December correctly', () => {
    expect(formatMonthYear(12, 2025)).toBe('December 2025')
  })
})
