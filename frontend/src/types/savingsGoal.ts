export interface SavingsGoal {
  id: string
  name: string
  target_amount: string
  current_amount: string
  target_date: string | null
  description: string | null
  progress_percentage: number
  is_on_track: boolean | null
  created_at: string
  updated_at: string
}

export interface SavingsGoalInput {
  name: string
  target_amount: string
  current_amount?: string
  target_date?: string | null
  description?: string | null
}
