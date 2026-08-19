export type NotificationType = 'unusual_spending'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  is_read: boolean
  related_transaction_id: string | null
  created_at: string
}
