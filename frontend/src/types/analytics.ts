import type { Category, CategoryType } from './category'
import type { RecurringFrequency } from './transaction'

export interface Summary {
  month: number
  year: number
  income: string
  expenses: string
  net_cash_flow: string
  previous_month_income: string
  previous_month_expenses: string
  income_change_percent: number | null
  expenses_change_percent: number | null
}

export interface CategoryBreakdownItem {
  category: Category
  amount: string
  transaction_count: number
  percent_of_total: number
}

export interface TrendItem {
  year: number
  month: number
  income: string
  expenses: string
  net_cash_flow: string
}

export interface MerchantItem {
  payee: string
  total_amount: string
  transaction_count: number
}

export interface RecurringSeriesItem {
  payee: string
  category: Category
  type: CategoryType
  amount: string
  frequency: RecurringFrequency
  last_date: string
  next_due_date: string
  transaction_id: string
}

export interface RecurringAnalysis {
  series: RecurringSeriesItem[]
  total_monthly_estimate: string
}
