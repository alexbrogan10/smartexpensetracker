import { Suspense, useState } from 'react'
import {
  AppBar,
  Badge,
  Box,
  Button,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import MenuIcon from '@mui/icons-material/Menu'
import NotificationsIcon from '@mui/icons-material/Notifications'
import { Link as RouterLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useNotifications } from '../hooks/useNotifications'

const NAV_LINKS = [
  { to: '/transactions', label: 'Transactions' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/savings-goals', label: 'Savings' },
  { to: '/reports', label: 'Reports' },
  { to: '/insights', label: 'Insights' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const { unreadCount } = useNotifications()
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar sx={{ gap: 2 }}>
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="open navigation menu"
              onClick={() => setDrawerOpen(true)}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{ flexGrow: 1, color: 'inherit', textDecoration: 'none' }}
          >
            Smart Expense Tracker
          </Typography>
          {!isMobile &&
            NAV_LINKS.map((link) => (
              <Button key={link.to} component={RouterLink} to={link.to} color="inherit">
                {link.label}
              </Button>
            ))}
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
          {!isMobile && (
            <Button component={RouterLink} to="/profile" color="inherit">
              {user?.full_name}
            </Button>
          )}
          {!isMobile && (
            <Button onClick={handleLogout} color="inherit">
              Log out
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 240 }} role="presentation" onClick={() => setDrawerOpen(false)}>
          <List>
            {NAV_LINKS.map((link) => (
              <ListItemButton key={link.to} component={RouterLink} to={link.to}>
                <ListItemText primary={link.label} />
              </ListItemButton>
            ))}
          </List>
          <Divider />
          <List>
            <ListItemButton component={RouterLink} to="/profile">
              <ListItemText primary={user?.full_name ?? 'Profile'} />
            </ListItemButton>
            <ListItemButton onClick={handleLogout}>
              <ListItemText primary="Log out" />
            </ListItemButton>
          </List>
        </Box>
      </Drawer>

      <Suspense
        fallback={
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
            <CircularProgress />
          </Box>
        }
      >
        <Outlet />
      </Suspense>
    </Box>
  )
}
