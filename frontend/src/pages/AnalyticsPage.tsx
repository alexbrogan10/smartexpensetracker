import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import * as analyticsApi from '../api/analytics'
import CategoryPieChart from '../components/charts/CategoryPieChart'
import TrendChart from '../components/charts/TrendChart'
import type { CategoryType } from '../types/category'
import type {
  CategoryBreakdownItem,
  MerchantItem,
  RecurringAnalysis,
  TrendItem,
} from '../types/analytics'
import { formatCurrency, formatDate, formatMonthYear } from '../utils/format'

const FREQUENCY_LABELS: Record<string, string> = {
  weekly: 'Weekly',
  biweekly: 'Biweekly',
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  yearly: 'Yearly',
}

export default function AnalyticsPage() {
  const today = new Date()
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [year, setYear] = useState(today.getFullYear())
  const [categoryType, setCategoryType] = useState<CategoryType>('expense')
  const [trendMonths, setTrendMonths] = useState(6)

  const [categories, setCategories] = useState<CategoryBreakdownItem[] | null>(null)
  const [merchants, setMerchants] = useState<MerchantItem[] | null>(null)
  const [trends, setTrends] = useState<TrendItem[] | null>(null)
  const [recurring, setRecurring] = useState<RecurringAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    analyticsApi
      .getCategoryBreakdown(year, month, categoryType)
      .then(setCategories)
      .catch(() => setError('Could not load category breakdown.'))
  }, [year, month, categoryType])

  useEffect(() => {
    analyticsApi
      .getTopMerchants(year, month, 10)
      .then(setMerchants)
      .catch(() => setError('Could not load top merchants.'))
  }, [year, month])

  useEffect(() => {
    analyticsApi
      .getTrends(trendMonths)
      .then(setTrends)
      .catch(() => setError('Could not load trends.'))
  }, [trendMonths])

  useEffect(() => {
    analyticsApi
      .getRecurringAnalysis()
      .then(setRecurring)
      .catch(() => setError('Could not load recurring analysis.'))
  }, [])

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

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Analytics
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Stack
            direction="row"
            sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
          >
            <Typography variant="subtitle1">Monthly trend</Typography>
            <TextField
              select
              size="small"
              value={trendMonths}
              onChange={(e) => setTrendMonths(Number(e.target.value))}
              sx={{ minWidth: 140 }}
            >
              <MenuItem value={6}>Last 6 months</MenuItem>
              <MenuItem value={12}>Last 12 months</MenuItem>
              <MenuItem value={24}>Last 24 months</MenuItem>
            </TextField>
          </Stack>
          {trends === null ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={28} />
            </Box>
          ) : (
            <TrendChart data={trends} height={300} />
          )}
        </CardContent>
      </Card>

      <Stack direction="row" sx={{ alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={goToPreviousMonth} aria-label="previous month">
          <ChevronLeftIcon />
        </IconButton>
        <Typography variant="h6" sx={{ minWidth: 200, textAlign: 'center' }}>
          {formatMonthYear(month, year)}
        </Typography>
        <IconButton onClick={goToNextMonth} aria-label="next month">
          <ChevronRightIcon />
        </IconButton>
      </Stack>

      <Stack direction="row" sx={{ gap: 2, flexWrap: 'wrap', alignItems: 'stretch', mb: 2 }}>
        <Card variant="outlined" sx={{ flex: '1 1 400px' }}>
          <CardContent>
            <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1">Spending by category</Typography>
              <TextField
                select
                size="small"
                value={categoryType}
                onChange={(e) => setCategoryType(e.target.value as CategoryType)}
                sx={{ minWidth: 120 }}
              >
                <MenuItem value="expense">Expense</MenuItem>
                <MenuItem value="income">Income</MenuItem>
              </TextField>
            </Stack>
            {categories === null ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={28} />
              </Box>
            ) : categories.length === 0 ? (
              <Typography color="text.secondary">No transactions for this month.</Typography>
            ) : (
              <>
                <CategoryPieChart data={categories} height={260} />
                <TableContainer sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Category</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell align="right">%</TableCell>
                        <TableCell align="right">Count</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {categories.map((item) => (
                        <TableRow key={item.category.id}>
                          <TableCell>{item.category.name}</TableCell>
                          <TableCell align="right">{formatCurrency(item.amount)}</TableCell>
                          <TableCell align="right">{item.percent_of_total}%</TableCell>
                          <TableCell align="right">{item.transaction_count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </CardContent>
        </Card>

        <Card variant="outlined" sx={{ flex: '1 1 320px' }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              Top merchants
            </Typography>
            {merchants === null ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={28} />
              </Box>
            ) : merchants.length === 0 ? (
              <Typography color="text.secondary">No expenses for this month.</Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Merchant</TableCell>
                      <TableCell align="right">Total</TableCell>
                      <TableCell align="right">Visits</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {merchants.map((m) => (
                      <TableRow key={m.payee}>
                        <TableCell>{m.payee}</TableCell>
                        <TableCell align="right">{formatCurrency(m.total_amount)}</TableCell>
                        <TableCell align="right">{m.transaction_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle1">Recurring expenses</Typography>
            {recurring && (
              <Typography variant="body2" color="text.secondary">
                Estimated {formatCurrency(recurring.total_monthly_estimate)}/month
              </Typography>
            )}
          </Stack>
          {recurring === null ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={28} />
            </Box>
          ) : recurring.series.length === 0 ? (
            <Typography color="text.secondary">No recurring transactions.</Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Payee</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Frequency</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Last</TableCell>
                    <TableCell>Next due</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recurring.series.map((item) => (
                    <TableRow key={item.transaction_id}>
                      <TableCell>{item.payee}</TableCell>
                      <TableCell>{item.category.name}</TableCell>
                      <TableCell>{FREQUENCY_LABELS[item.frequency]}</TableCell>
                      <TableCell align="right">{formatCurrency(item.amount)}</TableCell>
                      <TableCell>{formatDate(item.last_date)}</TableCell>
                      <TableCell>{formatDate(item.next_due_date)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
