import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import * as categoriesApi from '../api/categories'
import * as categorizationApi from '../api/categorization'
import * as transactionsApi from '../api/transactions'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import type { Category, CategoryType } from '../types/category'
import type { CategorySuggestion } from '../types/categorization'
import type { PaymentMethod, RecurringFrequency } from '../types/transaction'

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: 'cash', label: 'Cash' },
  { value: 'credit_card', label: 'Credit card' },
  { value: 'debit_card', label: 'Debit card' },
  { value: 'bank_transfer', label: 'Bank transfer' },
  { value: 'other', label: 'Other' },
]

const RECURRING_FREQUENCIES: { value: RecurringFrequency; label: string }[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Biweekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
]

export default function TransactionFormPage() {
  const { id } = useParams()
  const isEditing = Boolean(id)
  const navigate = useNavigate()

  const [categories, setCategories] = useState<Category[]>([])
  const [isLoadingTransaction, setIsLoadingTransaction] = useState(isEditing)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [type, setType] = useState<CategoryType>('expense')
  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  const [payee, setPayee] = useState('')
  const [description, setDescription] = useState('')
  const [transactionDate, setTransactionDate] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | ''>('')
  const [isRecurring, setIsRecurring] = useState(false)
  const [recurringFrequency, setRecurringFrequency] = useState<RecurringFrequency | ''>('')

  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [suggestion, setSuggestion] = useState<CategorySuggestion | null>(null)
  const debouncedPayee = useDebouncedValue(payee, 500)
  const debouncedDescription = useDebouncedValue(description, 500)

  useEffect(() => {
    categoriesApi
      .listCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    if (!debouncedPayee.trim()) {
      /* eslint-disable-next-line react-hooks/set-state-in-effect -- clearing a stale
         suggestion when the payee is emptied is a synchronous reset, not fetched state. */
      setSuggestion(null)
      return
    }
    let cancelled = false
    categorizationApi
      .suggestCategory({ type, payee: debouncedPayee, description: debouncedDescription || null })
      .then((response) => {
        if (cancelled) return
        setSuggestion(response.status === 'ok' ? (response.suggestions[0] ?? null) : null)
      })
      .catch(() => {
        if (!cancelled) setSuggestion(null)
      })
    return () => {
      cancelled = true
    }
  }, [type, debouncedPayee, debouncedDescription])

  useEffect(() => {
    if (!id) return
    transactionsApi
      .getTransaction(id)
      .then((t) => {
        setType(t.type)
        setCategoryId(t.category.id)
        setAmount(t.amount)
        setPayee(t.payee)
        setDescription(t.description ?? '')
        setTransactionDate(t.transaction_date)
        setPaymentMethod(t.payment_method ?? '')
        setIsRecurring(t.is_recurring)
        setRecurringFrequency(t.recurring_frequency ?? '')
      })
      .catch(() => setLoadError('Could not load this transaction.'))
      .finally(() => setIsLoadingTransaction(false))
  }, [id])

  const categoriesForType = categories.filter((c) => c.type === type)

  const handleTypeChange = (newType: CategoryType) => {
    setType(newType)
    setCategoryId('')
    setSuggestion(null)
    if (newType === 'income') {
      setPaymentMethod('')
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitError(null)
    setIsSubmitting(true)
    try {
      const payload = {
        type,
        category_id: categoryId,
        amount,
        payee,
        description: description || null,
        transaction_date: transactionDate,
        payment_method: type === 'expense' && paymentMethod ? paymentMethod : null,
        is_recurring: isRecurring,
        recurring_frequency: isRecurring && recurringFrequency ? recurringFrequency : null,
      }
      if (isEditing && id) {
        await transactionsApi.updateTransaction(id, payload)
      } else {
        await transactionsApi.createTransaction(payload)
      }
      navigate('/transactions')
    } catch {
      setSubmitError('Could not save this transaction. Please check the fields and try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoadingTransaction) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 4, maxWidth: 560 }}>
      <Typography variant="h4" gutterBottom>
        {isEditing ? 'Edit transaction' : 'Add transaction'}
      </Typography>

      {loadError && <Alert severity="error">{loadError}</Alert>}

      {!loadError && (
        <Paper component="form" onSubmit={handleSubmit} elevation={1} sx={{ p: 3, mt: 2 }}>
          {submitError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {submitError}
            </Alert>
          )}
          <Stack spacing={2}>
            <ToggleButtonGroup
              exclusive
              value={type}
              onChange={(_, value: CategoryType | null) => value && handleTypeChange(value)}
              fullWidth
            >
              <ToggleButton value="expense">Expense</ToggleButton>
              <ToggleButton value="income">Income</ToggleButton>
            </ToggleButtonGroup>

            <TextField
              select
              label="Category"
              required
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              {categoriesForType.map((c) => (
                <MenuItem key={c.id} value={c.id}>
                  {c.name}
                </MenuItem>
              ))}
            </TextField>

            {suggestion && suggestion.category_id !== categoryId && (
              <Alert
                severity="info"
                icon={<AutoAwesomeIcon fontSize="inherit" />}
                action={
                  <Button size="small" onClick={() => setCategoryId(suggestion.category_id)}>
                    Use
                  </Button>
                }
              >
                Suggested category: {suggestion.category_name} (
                {Math.round(suggestion.confidence * 100)}% confidence)
              </Alert>
            )}

            <TextField
              label="Amount"
              type="number"
              required
              slotProps={{ htmlInput: { step: '0.01', min: '0.01' } }}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />

            <TextField
              label={type === 'expense' ? 'Merchant' : 'Source'}
              required
              value={payee}
              onChange={(e) => setPayee(e.target.value)}
            />

            <TextField
              label="Description"
              multiline
              minRows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />

            <TextField
              label="Date"
              type="date"
              required
              slotProps={{ inputLabel: { shrink: true } }}
              value={transactionDate}
              onChange={(e) => setTransactionDate(e.target.value)}
            />

            {type === 'expense' && (
              <TextField
                select
                label="Payment method"
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
              >
                <MenuItem value="">—</MenuItem>
                {PAYMENT_METHODS.map((m) => (
                  <MenuItem key={m.value} value={m.value}>
                    {m.label}
                  </MenuItem>
                ))}
              </TextField>
            )}

            <FormControlLabel
              control={
                <Switch checked={isRecurring} onChange={(e) => setIsRecurring(e.target.checked)} />
              }
              label="Recurring"
            />

            {isRecurring && (
              <TextField
                select
                label="Frequency"
                required
                value={recurringFrequency}
                onChange={(e) => setRecurringFrequency(e.target.value as RecurringFrequency)}
              >
                {RECURRING_FREQUENCIES.map((f) => (
                  <MenuItem key={f.value} value={f.value}>
                    {f.label}
                  </MenuItem>
                ))}
              </TextField>
            )}

            <Stack direction="row" sx={{ gap: 2, justifyContent: 'flex-end', pt: 1 }}>
              <Button onClick={() => navigate('/transactions')} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" variant="contained" disabled={isSubmitting}>
                {isSubmitting ? 'Saving…' : 'Save'}
              </Button>
            </Stack>
          </Stack>
        </Paper>
      )}
    </Box>
  )
}
