import { createContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as notificationsApi from '../../api/notifications'

interface NotificationsContextValue {
  unreadCount: number
  refresh: () => Promise<void>
}

// eslint-disable-next-line react-refresh/only-export-components
export const NotificationsContext = createContext<NotificationsContextValue | null>(null)

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0)

  const refresh = async () => {
    const count = await notificationsApi.getUnreadCount()
    setUnreadCount(count)
  }

  useEffect(() => {
    // Fetch-on-mount: setState happens in the promise resolution, not
    // synchronously in the effect body.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh().catch(() => setUnreadCount(0))
  }, [])

  return (
    <NotificationsContext.Provider value={{ unreadCount, refresh }}>
      {children}
    </NotificationsContext.Provider>
  )
}
