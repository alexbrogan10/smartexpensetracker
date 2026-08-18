import type { Category, CategoryType } from './category'

export type PaymentMethod = 'cash' | 'credit_card' | 'debit_card' | 'bank_transfer' | 'other'

export type RecurringFrequency = 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'yearly'

export interface Transaction {
  id: string
  type: CategoryType
  category: Category
  amount: string
  payee: string
  description: string | null
  transaction_date: string
  payment_method: PaymentMethod | null
  is_recurring: boolean
  recurring_frequency: RecurringFrequency | null
  created_at: string
  updated_at: string
}

export interface TransactionInput {
  type: CategoryType
  category_id: string
  amount: string
  payee: string
  description?: string | null
  transaction_date: string
  payment_method?: PaymentMethod | null
  is_recurring: boolean
  recurring_frequency?: RecurringFrequency | null
}

export interface TransactionFilters {
  type?: CategoryType
  category_id?: string
  date_from?: string
  date_to?: string
  min_amount?: string
  max_amount?: string
  is_recurring?: boolean
  payment_method?: PaymentMethod
  search?: string
  sort_by?: 'transaction_date' | 'amount'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
