import { useContext } from 'react'
import { NotificationsContext } from '../features/notifications/NotificationsContext'

export function useNotifications() {
  const context = useContext(NotificationsContext)
  if (context === null) {
    throw new Error('useNotifications must be used within a NotificationsProvider')
  }
  return context
}
