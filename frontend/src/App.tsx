import { lazy, Suspense } from 'react'
import { Box, CircularProgress, CssBaseline, ThemeProvider } from '@mui/material'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './features/auth/AuthContext'
import { NotificationsProvider } from './features/notifications/NotificationsContext'
import { ToastProvider } from './features/toast/ToastContext'
import { theme } from './theme'

const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const BudgetsPage = lazy(() => import('./pages/BudgetsPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ImportPage = lazy(() => import('./pages/ImportPage'))
const InsightsPage = lazy(() => import('./pages/InsightsPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const SavingsGoalsPage = lazy(() => import('./pages/SavingsGoalsPage'))
const TransactionFormPage = lazy(() => import('./pages/TransactionFormPage'))
const TransactionsPage = lazy(() => import('./pages/TransactionsPage'))

function PageFallback() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
      <CircularProgress />
    </Box>
  )
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <ToastProvider>
          <AuthProvider>
            <Suspense fallback={<PageFallback />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route element={<ProtectedRoute />}>
                  <Route
                    element={
                      <NotificationsProvider>
                        <AppLayout />
                      </NotificationsProvider>
                    }
                  >
                    <Route path="/" element={<DashboardPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/budgets" element={<BudgetsPage />} />
                    <Route path="/savings-goals" element={<SavingsGoalsPage />} />
                    <Route path="/transactions" element={<TransactionsPage />} />
                    <Route path="/transactions/new" element={<TransactionFormPage />} />
                    <Route path="/transactions/:id/edit" element={<TransactionFormPage />} />
                    <Route path="/transactions/import" element={<ImportPage />} />
                    <Route path="/reports" element={<ReportsPage />} />
                    <Route path="/insights" element={<InsightsPage />} />
                    <Route path="/notifications" element={<NotificationsPage />} />
                    <Route path="/profile" element={<ProfilePage />} />
                  </Route>
                </Route>
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
