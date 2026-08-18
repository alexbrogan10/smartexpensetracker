import type { SavingsGoal, SavingsGoalInput } from '../types/savingsGoal'
import { apiClient } from './client'

export async function listSavingsGoals(): Promise<SavingsGoal[]> {
  const response = await apiClient.get<SavingsGoal[]>('/savings-goals')
  return response.data
}

export async function getSavingsGoal(id: string): Promise<SavingsGoal> {
  const response = await apiClient.get<SavingsGoal>(`/savings-goals/${id}`)
  return response.data
}

export async function createSavingsGoal(data: SavingsGoalInput): Promise<SavingsGoal> {
  const response = await apiClient.post<SavingsGoal>('/savings-goals', data)
  return response.data
}

export async function updateSavingsGoal(
  id: string,
  data: Partial<SavingsGoalInput>,
): Promise<SavingsGoal> {
  const response = await apiClient.put<SavingsGoal>(`/savings-goals/${id}`, data)
  return response.data
}

export async function deleteSavingsGoal(id: string): Promise<void> {
  await apiClient.delete(`/savings-goals/${id}`)
}
