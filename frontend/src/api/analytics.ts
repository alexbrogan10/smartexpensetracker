import type { CategoryType } from '../types/category'
import type {
  CategoryBreakdownItem,
  MerchantItem,
  RecurringAnalysis,
  Summary,
  TrendItem,
} from '../types/analytics'
import { apiClient } from './client'

export async function getSummary(year?: number, month?: number): Promise<Summary> {
  const response = await apiClient.get<Summary>('/analytics/summary', { params: { year, month } })
  return response.data
}

export async function getCategoryBreakdown(
  year?: number,
  month?: number,
  type: CategoryType = 'expense',
): Promise<CategoryBreakdownItem[]> {
  const response = await apiClient.get<CategoryBreakdownItem[]>('/analytics/categories', {
    params: { year, month, type },
  })
  return response.data
}

export async function getTrends(months = 6): Promise<TrendItem[]> {
  const response = await apiClient.get<TrendItem[]>('/analytics/trends', { params: { months } })
  return response.data
}

export async function getTopMerchants(
  year?: number,
  month?: number,
  limit = 10,
): Promise<MerchantItem[]> {
  const response = await apiClient.get<MerchantItem[]>('/analytics/merchants', {
    params: { year, month, limit },
  })
  return response.data
}

export async function getRecurringAnalysis(): Promise<RecurringAnalysis> {
  const response = await apiClient.get<RecurringAnalysis>('/analytics/recurring')
  return response.data
}
