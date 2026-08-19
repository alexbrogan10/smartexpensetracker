import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  Checkbox,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import * as importsApi from '../api/imports'
import type {
  ImportConfirmResult,
  ImportPreview,
  ImportRowStatus,
} from '../types/transactionImport'
import { formatCurrency, formatDate } from '../utils/format'

const STATUS_COLORS: Record<ImportRowStatus, 'success' | 'error' | 'warning'> = {
  valid: 'success',
  error: 'error',
  duplicate: 'warning',
}

export default function ImportPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [includeDuplicates, setIncludeDuplicates] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ImportConfirmResult | null>(null)

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setError(null)
    setResult(null)
    setIsUploading(true)
    try {
      const uploaded = await importsApi.uploadImport(file)
      setPreview(uploaded)
    } catch {
      setError('Could not read this file. Make sure it is a CSV with the expected columns.')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleConfirm = async () => {
    if (!preview) return
    setIsSubmitting(true)
    setError(null)
    try {
      const confirmResult = await importsApi.confirmImport(preview.id, includeDuplicates)
      setResult(confirmResult)
      setPreview(null)
    } catch {
      setError('Could not confirm this import. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancel = async () => {
    if (!preview) return
    setIsSubmitting(true)
    try {
      await importsApi.cancelImport(preview.id)
    } catch {
      // best-effort — the pending import is harmless to leave behind
    } finally {
      setPreview(null)
      setIncludeDuplicates(false)
      setIsSubmitting(false)
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 900 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Import transactions
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Imported {result.imported_count} transaction{result.imported_count === 1 ? '' : 's'}
          {result.skipped_count > 0 && ` (${result.skipped_count} skipped)`}.{' '}
          <Button size="small" onClick={() => navigate('/transactions')}>
            View transactions
          </Button>
        </Alert>
      )}

      {!preview && (
        <Paper variant="outlined" sx={{ p: 4 }}>
          <Stack spacing={2} sx={{ alignItems: 'flex-start' }}>
            <Button
              variant="contained"
              component="label"
              startIcon={
                isUploading ? <CircularProgress size={16} color="inherit" /> : <UploadFileIcon />
              }
              disabled={isUploading}
            >
              {isUploading ? 'Uploading…' : 'Choose CSV file'}
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                hidden
                onChange={handleFileChange}
              />
            </Button>

            <Typography variant="subtitle2" sx={{ mt: 2 }}>
              Expected columns
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Column</TableCell>
                    <TableCell>Required</TableCell>
                    <TableCell>Notes</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>date</TableCell>
                    <TableCell>Yes</TableCell>
                    <TableCell>YYYY-MM-DD or MM/DD/YYYY</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>type</TableCell>
                    <TableCell>Yes</TableCell>
                    <TableCell>income or expense</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>category</TableCell>
                    <TableCell>Yes</TableCell>
                    <TableCell>Must match an existing category name</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>payee</TableCell>
                    <TableCell>Yes</TableCell>
                    <TableCell>Merchant or income source</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>amount</TableCell>
                    <TableCell>Yes</TableCell>
                    <TableCell>Positive number</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>description</TableCell>
                    <TableCell>No</TableCell>
                    <TableCell />
                  </TableRow>
                  <TableRow>
                    <TableCell>payment_method</TableCell>
                    <TableCell>No</TableCell>
                    <TableCell>cash, credit_card, debit_card, bank_transfer, other</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>is_recurring / recurring_frequency</TableCell>
                    <TableCell>No</TableCell>
                    <TableCell>true/false, and weekly/biweekly/monthly/quarterly/yearly</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Stack>
        </Paper>
      )}

      {preview && (
        <Stack spacing={2}>
          <Stack direction="row" sx={{ gap: 1, flexWrap: 'wrap' }}>
            <Chip label={`${preview.total_rows} total`} />
            <Chip label={`${preview.valid_rows} valid`} color="success" />
            <Chip label={`${preview.error_rows} errors`} color="error" />
            <Chip label={`${preview.duplicate_rows} duplicates`} color="warning" />
          </Stack>

          {preview.duplicate_rows > 0 && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeDuplicates}
                  onChange={(e) => setIncludeDuplicates(e.target.checked)}
                />
              }
              label="Import duplicate rows anyway"
            />
          )}

          <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 480 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Row</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Payee</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {preview.rows.map((row) => (
                  <TableRow key={row.row_number} hover>
                    <TableCell>{row.row_number}</TableCell>
                    <TableCell>
                      <Chip size="small" label={row.status} color={STATUS_COLORS[row.status]} />
                    </TableCell>
                    <TableCell>
                      {row.fields ? formatDate(row.fields.transaction_date) : row.raw.date}
                    </TableCell>
                    <TableCell>{row.fields?.payee ?? row.raw.payee}</TableCell>
                    <TableCell align="right">
                      {row.fields ? formatCurrency(row.fields.amount) : row.raw.amount}
                    </TableCell>
                    <TableCell>
                      {row.errors.length > 0 ? (
                        <Typography variant="caption" color="text.secondary">
                          {row.errors.join('; ')}
                        </Typography>
                      ) : (
                        row.fields?.category_name
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Stack direction="row" sx={{ gap: 2, justifyContent: 'flex-end' }}>
            <Button onClick={handleCancel} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleConfirm}
              disabled={isSubmitting || preview.valid_rows === 0}
            >
              {isSubmitting ? 'Importing…' : 'Confirm import'}
            </Button>
          </Stack>
        </Stack>
      )}
    </Box>
  )
}
