import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TablePagination,
  Typography,
} from '@mui/material'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import * as notificationsApi from '../api/notifications'
import { useNotifications } from '../hooks/useNotifications'
import type { Notification } from '../types/notification'
import { formatDateTime } from '../utils/format'

export default function NotificationsPage() {
  const { refresh } = useNotifications()

  const [notifications, setNotifications] = useState<Notification[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- fetch-on-mount/page-change: loading
       state resets synchronously, results land in the promise resolution, not the effect body. */
    setIsLoading(true)
    setError(null)
    notificationsApi
      .listNotifications(false, page + 1, pageSize)
      .then((response) => {
        setNotifications(response.items)
        setTotal(response.total)
      })
      .catch(() => setError('Could not load notifications. Please try again.'))
      .finally(() => setIsLoading(false))
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [page, pageSize])

  const handleMarkAsRead = async (notification: Notification) => {
    if (notification.is_read) return
    try {
      await notificationsApi.markAsRead(notification.id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)),
      )
      await refresh()
    } catch {
      setError('Could not update this notification. Please try again.')
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      await refresh()
    } catch {
      setError('Could not mark all notifications as read. Please try again.')
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 800 }}>
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Notifications</Typography>
        <Button onClick={handleMarkAllAsRead} disabled={notifications.every((n) => n.is_read)}>
          Mark all read
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {!isLoading && notifications.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No notifications yet.</Typography>
        </Paper>
      )}

      {!isLoading && notifications.length > 0 && (
        <Paper variant="outlined">
          <Stack divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
            {notifications.map((notification) => (
              <Box
                key={notification.id}
                onClick={() => handleMarkAsRead(notification)}
                sx={{
                  p: 2,
                  cursor: notification.is_read ? 'default' : 'pointer',
                  bgcolor: notification.is_read ? 'transparent' : 'action.hover',
                }}
              >
                <Stack direction="row" sx={{ gap: 1.5, alignItems: 'flex-start' }}>
                  <WarningAmberIcon color="warning" fontSize="small" sx={{ mt: 0.3 }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography
                      variant="body2"
                      sx={{ fontWeight: notification.is_read ? 400 : 700 }}
                    >
                      {notification.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {notification.message}
                    </Typography>
                    <Stack direction="row" sx={{ gap: 2, alignItems: 'center', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {formatDateTime(notification.created_at)}
                      </Typography>
                      {notification.related_transaction_id && (
                        <Button
                          size="small"
                          component={RouterLink}
                          to={`/transactions/${notification.related_transaction_id}/edit`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          View transaction
                        </Button>
                      )}
                    </Stack>
                  </Box>
                </Stack>
              </Box>
            ))}
          </Stack>
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(Number(e.target.value))
              setPage(0)
            }}
            rowsPerPageOptions={[10, 25, 50]}
          />
        </Paper>
      )}
    </Box>
  )
}
