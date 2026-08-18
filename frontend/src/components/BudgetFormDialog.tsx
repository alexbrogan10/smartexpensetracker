import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import * as categoriesApi from '../api/categories'
import type { Budget, BudgetCategoryInput } from '../types/budget'
import type { Category } from '../types/category'
import { formatMonthYear } from '../utils/format'

interface BudgetFormDialogProps {
  open: boolean
  month: number
  year: number
  existingBudget: Budget | null
  onClose: () => void
  onSubmit: (overallAmount: string | null, categoryLimits: BudgetCategoryInput[]) => Promise<void>
}

export default function BudgetFormDialog({
  open,
  month,
  year,
  existingBudget,
  onClose,
  onSubmit,
}: BudgetFormDialogProps) {
  const [categories, setCategories] = useState<Category[]>([])
  const [overallAmount, setOverallAmount] = useState('')
  const [rows, setRows] = useState<BudgetCategoryInput[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    /* eslint-disable react-hooks/set-state-in-effect -- dialog-open reset: form
       fields are (re)initialized synchronously from props when the dialog opens;
       the category list itself lands via the promise resolution. */
    categoriesApi
      .listCategories('expense')
      .then(setCategories)
      .catch(() => setCategories([]))
    setOverallAmount(existingBudget?.overall_amount ?? '')
    setRows(
      existingBudget?.category_limits.map((l) => ({
        category_id: l.category.id,
        amount: l.amount,
      })) ?? [],
    )
    setError(null)
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [open, existingBudget])

  const addRow = () => {
    const unused = categories.find((c) => !rows.some((r) => r.category_id === c.id))
    if (!unused) return
    setRows([...rows, { category_id: unused.id, amount: '' }])
  }

  const updateRow = (index: number, patch: Partial<BudgetCategoryInput>) => {
    setRows(rows.map((r, i) => (i === index ? { ...r, ...patch } : r)))
  }

  const removeRow = (index: number) => {
    setRows(rows.filter((_, i) => i !== index))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    const incompleteRow = rows.some((r) => !r.category_id || !r.amount)
    if (incompleteRow) {
      setError('Every category row needs a category and an amount.')
      return
    }
    const categoryIds = rows.map((r) => r.category_id)
    if (new Set(categoryIds).size !== categoryIds.length) {
      setError('Each category can only appear once.')
      return
    }

    setIsSubmitting(true)
    try {
      await onSubmit(overallAmount || null, rows)
    } catch {
      setError('Could not save this budget. Please check the amounts and try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {existingBudget ? 'Edit' : 'Create'} budget — {formatMonthYear(month, year)}
      </DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Stack spacing={3}>
            <TextField
              label="Overall monthly budget"
              type="number"
              slotProps={{ htmlInput: { step: '0.01', min: '0.01' } }}
              value={overallAmount}
              onChange={(e) => setOverallAmount(e.target.value)}
              helperText="Optional overall spending ceiling for the month"
            />

            <Stack spacing={1}>
              <Typography variant="subtitle2">Category limits</Typography>
              {rows.map((row, index) => (
                <Stack key={index} direction="row" sx={{ gap: 1, alignItems: 'center' }}>
                  <TextField
                    select
                    label="Category"
                    size="small"
                    value={row.category_id}
                    onChange={(e) => updateRow(index, { category_id: e.target.value })}
                    sx={{ minWidth: 180 }}
                  >
                    {categories.map((c) => (
                      <MenuItem
                        key={c.id}
                        value={c.id}
                        disabled={rows.some((r, i) => i !== index && r.category_id === c.id)}
                      >
                        {c.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    label="Amount"
                    type="number"
                    size="small"
                    slotProps={{ htmlInput: { step: '0.01', min: '0.01' } }}
                    value={row.amount}
                    onChange={(e) => updateRow(index, { amount: e.target.value })}
                    sx={{ maxWidth: 120 }}
                  />
                  <IconButton size="small" onClick={() => removeRow(index)} aria-label="remove">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Stack>
              ))}
              <Button
                onClick={addRow}
                disabled={rows.length >= categories.length}
                sx={{ alignSelf: 'start' }}
              >
                Add category limit
              </Button>
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  )
}
