import { createContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Alert, Snackbar } from '@mui/material'

type ToastSeverity = 'success' | 'error'

interface ToastMessage {
  key: number
  message: string
  severity: ToastSeverity
}

interface ToastContextValue {
  showSuccess: (message: string) => void
  showError: (message: string) => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const ToastContext = createContext<ToastContextValue | null>(null)

let nextKey = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [queue, setQueue] = useState<ToastMessage[]>([])
  const [current, setCurrent] = useState<ToastMessage | null>(null)
  const [open, setOpen] = useState(false)

  const enqueue = (message: string, severity: ToastSeverity) => {
    setQueue((prev) => [...prev, { key: nextKey++, message, severity }])
  }

  useEffect(() => {
    // Drains the queue one toast at a time: a new message while one is
    // already showing closes it first, then the "exited" transition
    // callback below advances to the next. This mirrors MUI's own
    // consecutive-snackbars pattern, not a fetch-on-change effect.
    if (queue.length === 0) return
    if (current === null) {
      /* eslint-disable-next-line react-hooks/set-state-in-effect */
      setCurrent(queue[0])
      setQueue((prev) => prev.slice(1))
      setOpen(true)
    } else if (open) {
      setOpen(false)
    }
  }, [queue, current, open])

  const handleClose = (_: unknown, reason?: string) => {
    if (reason === 'clickaway') return
    setOpen(false)
  }

  const handleExited = () => {
    setCurrent(null)
  }

  return (
    <ToastContext.Provider
      value={{
        showSuccess: (message) => enqueue(message, 'success'),
        showError: (message) => enqueue(message, 'error'),
      }}
    >
      {children}
      <Snackbar
        key={current?.key}
        open={open}
        autoHideDuration={4000}
        onClose={handleClose}
        slotProps={{ transition: { onExited: handleExited } }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {current ? (
          <Alert onClose={handleClose} severity={current.severity} variant="filled">
            {current.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </ToastContext.Provider>
  )
}
