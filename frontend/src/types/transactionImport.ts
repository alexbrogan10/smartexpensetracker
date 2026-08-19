import type { CategoryType } from './category'
import type { PaymentMethod, RecurringFrequency } from './transaction'

export type ImportStatus = 'pending' | 'confirmed' | 'cancelled'
export type ImportRowStatus = 'valid' | 'error' | 'duplicate'

export interface ParsedTransactionFields {
  type: CategoryType
  category_id: string
  category_name: string
  amount: string
  payee: string
  description: string | null
  transaction_date: string
  payment_method: PaymentMethod | null
  is_recurring: boolean
  recurring_frequency: RecurringFrequency | null
}

export interface ImportRowPreview {
  row_number: number
  raw: Record<string, string>
  status: ImportRowStatus
  errors: string[]
  fields: ParsedTransactionFields | null
}

export interface ImportPreview {
  id: string
  filename: string
  status: ImportStatus
  total_rows: number
  valid_rows: number
  error_rows: number
  duplicate_rows: number
  rows: ImportRowPreview[]
  created_at: string
}

export interface ImportConfirmResult {
  imported_count: number
  skipped_count: number
}
