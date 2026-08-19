import type { CategorySuggestionRequest, CategorySuggestionResponse } from '../types/categorization'
import { apiClient } from './client'

export async function suggestCategory(
  request: CategorySuggestionRequest,
): Promise<CategorySuggestionResponse> {
  const response = await apiClient.post<CategorySuggestionResponse>(
    '/categorization/suggest',
    request,
  )
  return response.data
}
