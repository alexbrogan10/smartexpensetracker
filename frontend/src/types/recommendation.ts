export type RecommendationType = 'budget_pace' | 'category_trend' | 'savings_off_track'
export type RecommendationSeverity = 'info' | 'warning' | 'critical'

export interface Recommendation {
  type: RecommendationType
  severity: RecommendationSeverity
  message: string
  category_id: string | null
  goal_id: string | null
}
