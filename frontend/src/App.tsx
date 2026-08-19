import { CssBaseline, ThemeProvider } from '@mui/material'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './features/auth/AuthContext'
import { NotificationsProvider } from './features/notifications/NotificationsContext'
import AnalyticsPage from './pages/AnalyticsPage'
import BudgetsPage from './pages/BudgetsPage'
import DashboardPage from './pages/DashboardPage'
import ImportPage from './pages/ImportPage'
import InsightsPage from './pages/InsightsPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import NotificationsPage from './pages/NotificationsPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import ReportsPage from './pages/ReportsPage'
import SavingsGoalsPage from './pages/SavingsGoalsPage'
import TransactionFormPage from './pages/TransactionFormPage'
import TransactionsPage from './pages/TransactionsPage'
import { theme } from './theme'

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
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
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
