import type { Recommendation } from '../types/recommendation'
import { apiClient } from './client'

export async function getRecommendations(): Promise<Recommendation[]> {
  const response = await apiClient.get<{ recommendations: Recommendation[] }>('/recommendations')
  return response.data.recommendations
}
