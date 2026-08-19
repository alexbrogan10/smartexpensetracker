export interface CategoryPrediction {
  category_id: string
  category_name: string
  predicted_amount: string
}

export interface SpendingPrediction {
  status: 'ok' | 'insufficient_data'
  next_month: string
  predicted_income: string | null
  predicted_expenses: string | null
  by_category: CategoryPrediction[]
}
