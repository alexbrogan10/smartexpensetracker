import type { Category, CategoryType } from '../types/category'
import { apiClient } from './client'

export async function listCategories(type?: CategoryType): Promise<Category[]> {
  const response = await apiClient.get<Category[]>('/categories', { params: { type } })
  return response.data
}
