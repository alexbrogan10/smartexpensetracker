export type CategoryType = 'income' | 'expense'

export interface Category {
  id: string
  user_id: string | null
  name: string
  type: CategoryType
  icon: string | null
  color: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}
