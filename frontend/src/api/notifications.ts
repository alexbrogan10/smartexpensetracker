import type { Notification } from '../types/notification'
import type { PaginatedResponse } from '../types/transaction'
import { apiClient } from './client'

export async function listNotifications(
  unreadOnly = false,
  page = 1,
  pageSize = 25,
): Promise<PaginatedResponse<Notification>> {
  const response = await apiClient.get<PaginatedResponse<Notification>>('/notifications', {
    params: { unread_only: unreadOnly, page, page_size: pageSize },
  })
  return response.data
}

export async function getUnreadCount(): Promise<number> {
  const response = await apiClient.get<{ count: number }>('/notifications/unread-count')
  return response.data.count
}

export async function markAsRead(notificationId: string): Promise<Notification> {
  const response = await apiClient.patch<Notification>(`/notifications/${notificationId}/read`)
  return response.data
}

export async function markAllAsRead(): Promise<number> {
  const response = await apiClient.post<{ marked_read: number }>('/notifications/read-all')
  return response.data.marked_read
}
