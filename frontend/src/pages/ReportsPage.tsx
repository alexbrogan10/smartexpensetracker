import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import * as categoriesApi from '../api/categories'
import * as reportsApi from '../api/reports'
import type { Category } from '../types/category'

export default function ReportsPage() {
  const [categories, setCategories] = useState<Category[]>([])

  const [type, setType] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')
  const [recurringOnly, setRecurringOnly] = useState(false)
  const [format, setFormat] = useState<reportsApi.ExportFormat>('csv')

  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    categoriesApi
      .listCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
  }, [])

  const handleExport = async () => {
    setIsExporting(true)
    setError(null)
    try {
      await reportsApi.exportTransactions(format, {
        type: (type || undefined) as 'income' | 'expense' | undefined,
        category_id: categoryId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        min_amount: minAmount || undefined,
        max_amount: maxAmount || undefined,
        is_recurring: recurringOnly || undefined,
      })
    } catch {
      setError('Could not export transactions. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 700 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Reports
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>
          Export transactions
        </Typography>
        <Stack spacing={2}>
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 2 }}>
            <TextField
              select
              label="Type"
              size="small"
              value={type}
              onChange={(e) => setType(e.target.value)}
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
              onChange={(e) => setCategoryId(e.target.value)}
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
              onChange={(e) => setDateFrom(e.target.value)}
            />
            <TextField
              label="To"
              type="date"
              size="small"
              slotProps={{ inputLabel: { shrink: true } }}
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
            <TextField
              label="Min amount"
              type="number"
              size="small"
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              sx={{ maxWidth: 120 }}
            />
            <TextField
              label="Max amount"
              type="number"
              size="small"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              sx={{ maxWidth: 120 }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={recurringOnly}
                  onChange={(e) => setRecurringOnly(e.target.checked)}
                />
              }
              label="Recurring only"
            />
          </Stack>

          <TextField
            select
            label="Format"
            size="small"
            value={format}
            onChange={(e) => setFormat(e.target.value as reportsApi.ExportFormat)}
            sx={{ maxWidth: 160 }}
          >
            <MenuItem value="csv">CSV</MenuItem>
            <MenuItem value="xlsx">Excel (.xlsx)</MenuItem>
          </TextField>

          <Box>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleExport}
              disabled={isExporting}
            >
              {isExporting ? 'Exporting…' : 'Export'}
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Box>
  )
}
