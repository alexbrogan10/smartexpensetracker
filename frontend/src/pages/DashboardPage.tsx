import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward'
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward'
import * as analyticsApi from '../api/analytics'
import * as budgetsApi from '../api/budgets'
import * as savingsGoalsApi from '../api/savingsGoals'
import * as transactionsApi from '../api/transactions'
import CategoryPieChart from '../components/charts/CategoryPieChart'
import TrendChart from '../components/charts/TrendChart'
import type { Budget } from '../types/budget'
import type {
  CategoryBreakdownItem,
  RecurringAnalysis,
  Summary,
  TrendItem,
} from '../types/analytics'
import type { SavingsGoal } from '../types/savingsGoal'
import type { Transaction } from '../types/transaction'
import { formatCurrency, formatDate } from '../utils/format'
import { STATUS_CRITICAL, STATUS_GOOD } from '../utils/chartColors'

interface DashboardData {
  summary: Summary
  categories: CategoryBreakdownItem[]
  trends: TrendItem[]
  recentTransactions: Transaction[]
  budget: Budget | null
  savingsGoals: SavingsGoal[]
  recurring: RecurringAnalysis
}

function ChangeIndicator({ percent }: { percent: number | null }) {
  if (percent === null) return null
  const isUp = percent >= 0
  return (
    <Stack direction="row" sx={{ alignItems: 'center', gap: 0.25 }}>
      {isUp ? (
        <ArrowUpwardIcon fontSize="inherit" sx={{ color: STATUS_GOOD }} />
      ) : (
        <ArrowDownwardIcon fontSize="inherit" sx={{ color: STATUS_CRITICAL }} />
      )}
      <Typography variant="caption" sx={{ color: isUp ? STATUS_GOOD : STATUS_CRITICAL }}>
        {Math.abs(percent).toFixed(1)}% vs last month
      </Typography>
    </Stack>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      analyticsApi.getSummary(),
      analyticsApi.getCategoryBreakdown(),
      analyticsApi.getTrends(6),
      transactionsApi.listTransactions({ page: 1, page_size: 5 }),
      budgetsApi.getCurrentBudget(),
      savingsGoalsApi.listSavingsGoals(),
      analyticsApi.getRecurringAnalysis(),
    ])
      .then(([summary, categories, trends, transactions, budget, savingsGoals, recurring]) => {
        setData({
          summary,
          categories,
          trends,
          recentTransactions: transactions.items,
          budget,
          savingsGoals,
          recurring,
        })
      })
      .catch(() => setError('Could not load your dashboard. Please try again.'))
  }, [])

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <CircularProgress />
      </Box>
    )
  }

  const { summary, categories, trends, recentTransactions, budget, savingsGoals, recurring } = data
  const upcomingRecurring = recurring.series.slice(0, 5)

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Dashboard
      </Typography>

      <Stack direction="row" sx={{ gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Card variant="outlined" sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Income this month
            </Typography>
            <Typography variant="h5">{formatCurrency(summary.income)}</Typography>
            <ChangeIndicator percent={summary.income_change_percent} />
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Expenses this month
            </Typography>
            <Typography variant="h5">{formatCurrency(summary.expenses)}</Typography>
            <ChangeIndicator percent={summary.expenses_change_percent} />
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Net cash flow
            </Typography>
            <Typography
              variant="h5"
              sx={{ color: Number(summary.net_cash_flow) >= 0 ? STATUS_GOOD : STATUS_CRITICAL }}
            >
              {formatCurrency(summary.net_cash_flow)}
            </Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: '1 1 200px' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              Budget this month
            </Typography>
            {budget?.overall_amount ? (
              <>
                <Typography variant="h5">
                  {formatCurrency(budget.overall_remaining ?? '0')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  remaining of {formatCurrency(budget.overall_amount)}
                </Typography>
              </>
            ) : (
              <Button size="small" component={RouterLink} to="/budgets" sx={{ mt: 1 }}>
                Set a budget
              </Button>
            )}
          </CardContent>
        </Card>
      </Stack>

      <Stack direction="row" sx={{ gap: 2, flexWrap: 'wrap', alignItems: 'stretch' }}>
        <Box sx={{ flex: '2 1 480px', minWidth: 320 }}>
          <Stack spacing={2}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Income vs expenses
                </Typography>
                <TrendChart data={trends} />
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Spending by category
                </Typography>
                {categories.length === 0 ? (
                  <Typography color="text.secondary">No expenses recorded this month.</Typography>
                ) : (
                  <CategoryPieChart data={categories} />
                )}
              </CardContent>
            </Card>
          </Stack>
        </Box>

        <Box sx={{ flex: '1 1 320px', minWidth: 300 }}>
          <Stack spacing={2}>
            <Card variant="outlined">
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1">Recent transactions</Typography>
                  <Button size="small" component={RouterLink} to="/transactions">
                    View all
                  </Button>
                </Stack>
                {recentTransactions.length === 0 ? (
                  <Typography color="text.secondary">No transactions yet.</Typography>
                ) : (
                  <Stack divider={<Divider />} spacing={1}>
                    {recentTransactions.map((t) => (
                      <Stack key={t.id} direction="row" sx={{ justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body2">{t.payee}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(t.transaction_date)} · {t.category.name}
                          </Typography>
                        </Box>
                        <Typography
                          variant="body2"
                          sx={{ color: t.type === 'income' ? STATUS_GOOD : 'text.primary' }}
                        >
                          {t.type === 'income' ? '+' : '-'}
                          {formatCurrency(t.amount)}
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  Upcoming recurring
                </Typography>
                {upcomingRecurring.length === 0 ? (
                  <Typography color="text.secondary">No recurring transactions.</Typography>
                ) : (
                  <Stack divider={<Divider />} spacing={1}>
                    {upcomingRecurring.map((item) => (
                      <Stack
                        key={item.transaction_id}
                        direction="row"
                        sx={{ justifyContent: 'space-between' }}
                      >
                        <Box>
                          <Typography variant="body2">{item.payee}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Due {formatDate(item.next_due_date)}
                          </Typography>
                        </Box>
                        <Typography variant="body2">{formatCurrency(item.amount)}</Typography>
                      </Stack>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>

            <Card variant="outlined">
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1">Savings goals</Typography>
                  <Button size="small" component={RouterLink} to="/savings-goals">
                    View all
                  </Button>
                </Stack>
                {savingsGoals.length === 0 ? (
                  <Typography color="text.secondary">No savings goals yet.</Typography>
                ) : (
                  <Stack spacing={1.5}>
                    {savingsGoals.slice(0, 3).map((goal) => (
                      <Box key={goal.id}>
                        <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
                          <Typography variant="body2">{goal.name}</Typography>
                          {goal.is_on_track !== null && (
                            <Chip
                              size="small"
                              label={goal.is_on_track ? 'On track' : 'Behind'}
                              color={goal.is_on_track ? 'success' : 'warning'}
                            />
                          )}
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={goal.progress_percentage}
                          sx={{ height: 6, borderRadius: 3, my: 0.5 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatCurrency(goal.current_amount)} of{' '}
                          {formatCurrency(goal.target_amount)}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Box>
      </Stack>
    </Box>
  )
}
