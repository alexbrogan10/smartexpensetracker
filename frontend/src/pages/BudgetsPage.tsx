import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import * as budgetsApi from '../api/budgets'
import BudgetFormDialog from '../components/BudgetFormDialog'
import ConfirmDialog from '../components/ConfirmDialog'
import type { Budget, BudgetCategoryInput, BudgetStatus } from '../types/budget'
import { formatCurrency, formatMonthYear } from '../utils/format'

function statusColor(status: BudgetStatus): 'success' | 'warning' | 'error' {
  if (status === 'exceeded') return 'error'
  if (status === 'warning') return 'warning'
  return 'success'
}

export default function BudgetsPage() {
  const today = new Date()
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [year, setYear] = useState(today.getFullYear())

  const [budget, setBudget] = useState<Budget | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const load = () => {
    setIsLoading(true)
    setError(null)
    budgetsApi
      .listBudgets(year)
      .then((budgets) => setBudget(budgets.find((b) => b.month === month) ?? null))
      .catch(() => setError('Could not load this budget. Please try again.'))
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    /* eslint-disable-next-line react-hooks/set-state-in-effect -- fetch-on-month-change:
       loading state resets synchronously, results land in the promise resolution. */
    load()
    // load() reads month/year via closure; both are already effect dependencies below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month, year])

  const goToPreviousMonth = () => {
    if (month === 1) {
      setMonth(12)
      setYear(year - 1)
    } else {
      setMonth(month - 1)
    }
  }

  const goToNextMonth = () => {
    if (month === 12) {
      setMonth(1)
      setYear(year + 1)
    } else {
      setMonth(month + 1)
    }
  }

  const handleFormSubmit = async (
    overallAmount: string | null,
    categoryLimits: BudgetCategoryInput[],
  ) => {
    if (budget) {
      await budgetsApi.updateBudget(budget.id, {
        overall_amount: overallAmount,
        category_limits: categoryLimits,
      })
    } else {
      await budgetsApi.createBudget({
        month,
        year,
        overall_amount: overallAmount,
        category_limits: categoryLimits,
      })
    }
    setIsFormOpen(false)
    load()
  }

  const handleDelete = async () => {
    if (!budget) return
    setIsDeleting(true)
    try {
      await budgetsApi.deleteBudget(budget.id)
      setIsDeleteOpen(false)
      load()
    } catch {
      setError('Could not delete this budget. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 720 }}>
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Stack direction="row" sx={{ alignItems: 'center', gap: 1 }}>
          <IconButton onClick={goToPreviousMonth} aria-label="previous month">
            <ChevronLeftIcon />
          </IconButton>
          <Typography variant="h5" sx={{ minWidth: 200, textAlign: 'center' }}>
            {formatMonthYear(month, year)}
          </Typography>
          <IconButton onClick={goToNextMonth} aria-label="next month">
            <ChevronRightIcon />
          </IconButton>
        </Stack>
        {budget && (
          <Stack direction="row" sx={{ gap: 1 }}>
            <Button onClick={() => setIsFormOpen(true)}>Edit</Button>
            <Button color="error" onClick={() => setIsDeleteOpen(true)}>
              Delete
            </Button>
          </Stack>
        )}
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

      {!isLoading && !budget && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              No budget set for {formatMonthYear(month, year)}.
            </Typography>
            <Button variant="contained" onClick={() => setIsFormOpen(true)}>
              Create budget
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && budget && (
        <Stack spacing={2}>
          {budget.overall_amount && (
            <Card variant="outlined">
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1">Overall budget</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatCurrency(budget.overall_spent)} of{' '}
                    {formatCurrency(budget.overall_amount)}
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(100, budget.overall_percent_used ?? 0)}
                  color={statusColor(budget.overall_status)}
                  sx={{ height: 8, borderRadius: 4, mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  {budget.overall_remaining && Number(budget.overall_remaining) >= 0
                    ? `${formatCurrency(budget.overall_remaining)} remaining`
                    : `${formatCurrency(String(Math.abs(Number(budget.overall_remaining))))} over budget`}
                </Typography>
              </CardContent>
            </Card>
          )}

          {budget.category_limits.map((limit) => (
            <Card key={limit.id} variant="outlined">
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle1">{limit.category.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatCurrency(limit.spent)} of {formatCurrency(limit.amount)}
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(100, limit.percent_used)}
                  color={statusColor(limit.status)}
                  sx={{ height: 8, borderRadius: 4, mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  {Number(limit.remaining) >= 0
                    ? `${formatCurrency(limit.remaining)} remaining`
                    : `${formatCurrency(String(Math.abs(Number(limit.remaining))))} over budget`}
                </Typography>
              </CardContent>
            </Card>
          ))}

          {budget.category_limits.length === 0 && !budget.overall_amount && (
            <Typography color="text.secondary">
              This budget has no overall amount or category limits set yet.
            </Typography>
          )}
        </Stack>
      )}

      <BudgetFormDialog
        open={isFormOpen}
        month={month}
        year={year}
        existingBudget={budget}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
      />

      <ConfirmDialog
        open={isDeleteOpen}
        title="Delete budget?"
        message={`This will remove the budget for ${formatMonthYear(month, year)}.`}
        isConfirming={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setIsDeleteOpen(false)}
      />
    </Box>
  )
}
