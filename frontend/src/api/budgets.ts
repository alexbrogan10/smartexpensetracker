import type { Budget, BudgetInput } from '../types/budget'
import { apiClient } from './client'

export async function listBudgets(year?: number): Promise<Budget[]> {
  const response = await apiClient.get<Budget[]>('/budgets', { params: { year } })
  return response.data
}

export async function getCurrentBudget(): Promise<Budget | null> {
  const response = await apiClient.get<Budget | null>('/budgets/current')
  return response.data
}

export async function getBudget(id: string): Promise<Budget> {
  const response = await apiClient.get<Budget>(`/budgets/${id}`)
  return response.data
}

export async function createBudget(data: BudgetInput): Promise<Budget> {
  const response = await apiClient.post<Budget>('/budgets', data)
  return response.data
}

export async function updateBudget(id: string, data: Partial<BudgetInput>): Promise<Budget> {
  const response = await apiClient.put<Budget>(`/budgets/${id}`, data)
  return response.data
}

export async function deleteBudget(id: string): Promise<void> {
  await apiClient.delete(`/budgets/${id}`)
}
