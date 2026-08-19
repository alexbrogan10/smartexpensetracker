import type { SpendingPrediction } from '../types/prediction'
import { apiClient } from './client'

export async function getSpendingPrediction(): Promise<SpendingPrediction> {
  const response = await apiClient.get<SpendingPrediction>('/predictions/spending')
  return response.data
}
