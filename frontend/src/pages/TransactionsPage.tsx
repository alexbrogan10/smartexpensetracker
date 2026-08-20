import { useEffect, useMemo, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import * as categoriesApi from '../api/categories'
import * as transactionsApi from '../api/transactions'
import ConfirmDialog from '../components/ConfirmDialog'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { useToast } from '../hooks/useToast'
import type { Category } from '../types/category'
import type { Transaction } from '../types/transaction'
import { formatCurrency, formatDate } from '../utils/format'

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  cash: 'Cash',
  credit_card: 'Credit card',
  debit_card: 'Debit card',
  bank_transfer: 'Bank transfer',
  other: 'Other',
}

export default function TransactionsPage() {
  const { showSuccess, showError } = useToast()
  const [categories, setCategories] = useState<Category[]>([])

  const [searchInput, setSearchInput] = useState('')
  const search = useDebouncedValue(searchInput)
  const [type, setType] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')
  const [recurringOnly, setRecurringOnly] = useState(false)

  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)

  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    categoriesApi
      .listCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  const filters = useMemo(
    () => ({
      search: search || undefined,
      type: (type || undefined) as 'income' | 'expense' | undefined,
      category_id: categoryId || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      min_amount: minAmount || undefined,
      max_amount: maxAmount || undefined,
      is_recurring: recurringOnly || undefined,
      page: page + 1,
      page_size: pageSize,
    }),
    [
      search,
      type,
      categoryId,
      dateFrom,
      dateTo,
      minAmount,
      maxAmount,
      recurringOnly,
      page,
      pageSize,
    ],
  )

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- fetch-on-filter-change: loading/error
       state intentionally resets synchronously when filters change, and results land in
       the promise resolution, not synchronously in the effect body. */
    setIsLoading(true)
    setError(null)
    transactionsApi
      .listTransactions(filters)
      .then((response) => {
        setTransactions(response.items)
        setTotal(response.total)
      })
      .catch(() => setError('Could not load transactions. Please try again.'))
      .finally(() => setIsLoading(false))
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [filters])

  const handleClearFilters = () => {
    setSearchInput('')
    setType('')
    setCategoryId('')
    setDateFrom('')
    setDateTo('')
    setMinAmount('')
    setMaxAmount('')
    setRecurringOnly(false)
    setPage(0)
  }

  const handleConfirmDelete = async () => {
    if (!pendingDeleteId) return
    setIsDeleting(true)
    try {
      await transactionsApi.deleteTransaction(pendingDeleteId)
      setPendingDeleteId(null)
      const response = await transactionsApi.listTransactions(filters)
      setTransactions(response.items)
      setTotal(response.total)
      showSuccess('Transaction deleted.')
    } catch {
      showError('Could not delete transaction. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Box sx={{ p: 4 }}>
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Transactions</Typography>
        <Stack direction="row" sx={{ gap: 1 }}>
          <Button component={RouterLink} to="/transactions/import">
            Import CSV
          </Button>
          <Button component={RouterLink} to="/transactions/new" variant="contained">
            Add transaction
          </Button>
        </Stack>
      </Stack>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 2 }}>
          <TextField
            label="Search"
            size="small"
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value)
              setPage(0)
            }}
            sx={{ minWidth: 200 }}
          />
          <TextField
            select
            label="Type"
            size="small"
            value={type}
            onChange={(e) => {
              setType(e.target.value)
              setPage(0)
            }}
            sx={{ minWidth: 140 }}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="expense">Expense</MenuItem>
            <MenuItem value="income">Income</MenuItem>
          </TextField>
          <TextField
            select
            label="Category"
            size="small"
            value={categoryId}
            onChange={(e) => {
              setCategoryId(e.target.value)
              setPage(0)
            }}
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="">All</MenuItem>
            {categories
              .filter((c) => !type || c.type === type)
              .map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
          </TextField>
          <TextField
            label="From"
            type="date"
            size="small"
            slotProps={{ inputLabel: { shrink: true } }}
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value)
              setPage(0)
            }}
          />
          <TextField
            label="To"
            type="date"
            size="small"
            slotProps={{ inputLabel: { shrink: true } }}
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value)
              setPage(0)
            }}
          />
          <TextField
            label="Min amount"
            type="number"
            size="small"
            value={minAmount}
            onChange={(e) => {
              setMinAmount(e.target.value)
              setPage(0)
            }}
            sx={{ maxWidth: 120 }}
          />
          <TextField
            label="Max amount"
            type="number"
            size="small"
            value={maxAmount}
            onChange={(e) => {
              setMaxAmount(e.target.value)
              setPage(0)
            }}
            sx={{ maxWidth: 120 }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={recurringOnly}
                onChange={(e) => {
                  setRecurringOnly(e.target.checked)
                  setPage(0)
                }}
              />
            }
            label="Recurring only"
          />
          <Button onClick={handleClearFilters}>Clear filters</Button>
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Payee</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Payment method</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <CircularProgress size={28} />
                </TableCell>
              </TableRow>
            )}
            {!isLoading && transactions.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">No transactions found.</Typography>
                </TableCell>
              </TableRow>
            )}
            {!isLoading &&
              transactions.map((t) => (
                <TableRow key={t.id} hover>
                  <TableCell>{formatDate(t.transaction_date)}</TableCell>
                  <TableCell>{t.payee}</TableCell>
                  <TableCell>{t.category.name}</TableCell>
                  <TableCell>
                    {t.payment_method ? PAYMENT_METHOD_LABELS[t.payment_method] : '—'}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: t.type === 'income' ? 'success.main' : 'text.primary' }}
                  >
                    {t.type === 'income' ? '+' : '-'}
                    {formatCurrency(t.amount)}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      component={RouterLink}
                      to={`/transactions/${t.id}/edit`}
                      size="small"
                      aria-label="edit"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      aria-label="delete"
                      onClick={() => setPendingDeleteId(t.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
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
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="Delete transaction?"
        message="This action cannot be undone."
        isConfirming={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setPendingDeleteId(null)}
      />
    </Box>
  )
}
