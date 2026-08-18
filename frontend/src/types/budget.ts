import type { Category } from './category'

export type BudgetStatus = 'ok' | 'warning' | 'exceeded'

export interface BudgetCategoryLimit {
  id: string
  category: Category
  amount: string
  spent: string
  remaining: string
  percent_used: number
  status: BudgetStatus
}

export interface Budget {
  id: string
  month: number
  year: number
  overall_amount: string | null
  overall_spent: string
  overall_remaining: string | null
  overall_percent_used: number | null
  overall_status: BudgetStatus
  category_limits: BudgetCategoryLimit[]
  created_at: string
  updated_at: string
}

export interface BudgetCategoryInput {
  category_id: string
  amount: string
}

export interface BudgetInput {
  month: number
  year: number
  overall_amount?: string | null
  category_limits?: BudgetCategoryInput[]
}
