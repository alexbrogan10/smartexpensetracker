import { AppBar, Badge, Box, Button, IconButton, Toolbar, Typography } from '@mui/material'
import NotificationsIcon from '@mui/icons-material/Notifications'
import { Link as RouterLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useNotifications } from '../hooks/useNotifications'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const { unreadCount } = useNotifications()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ gap: 2 }}>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{ flexGrow: 1, color: 'inherit', textDecoration: 'none' }}
          >
            Smart Expense Tracker
          </Typography>
          <Button component={RouterLink} to="/transactions" color="inherit">
            Transactions
          </Button>
          <Button component={RouterLink} to="/analytics" color="inherit">
            Analytics
          </Button>
          <Button component={RouterLink} to="/budgets" color="inherit">
            Budgets
          </Button>
          <Button component={RouterLink} to="/savings-goals" color="inherit">
            Savings
          </Button>
          <Button component={RouterLink} to="/reports" color="inherit">
            Reports
          </Button>
          <Button component={RouterLink} to="/insights" color="inherit">
            Insights
          </Button>
          <IconButton
            component={RouterLink}
            to="/notifications"
            color="inherit"
            aria-label="notifications"
          >
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          <Button component={RouterLink} to="/profile" color="inherit">
            {user?.full_name}
          </Button>
          <Button onClick={handleLogout} color="inherit">
            Log out
          </Button>
        </Toolbar>
      </AppBar>
      <Outlet />
    </Box>
  )
}
