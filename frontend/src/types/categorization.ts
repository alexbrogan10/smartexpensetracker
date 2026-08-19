import type { CategoryType } from './category'

export interface CategorySuggestionRequest {
  type: CategoryType
  payee: string
  description?: string | null
}

export interface CategorySuggestion {
  category_id: string
  category_name: string
  confidence: number
}

export interface CategorySuggestionResponse {
  status: 'ok' | 'insufficient_data'
  suggestions: CategorySuggestion[]
}
