import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material'
import type { SavingsGoal, SavingsGoalInput } from '../types/savingsGoal'

interface SavingsGoalFormDialogProps {
  open: boolean
  existingGoal: SavingsGoal | null
  onClose: () => void
  onSubmit: (data: SavingsGoalInput) => Promise<void>
}

export default function SavingsGoalFormDialog({
  open,
  existingGoal,
  onClose,
  onSubmit,
}: SavingsGoalFormDialogProps) {
  const [name, setName] = useState('')
  const [targetAmount, setTargetAmount] = useState('')
  const [currentAmount, setCurrentAmount] = useState('')
  const [targetDate, setTargetDate] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    /* eslint-disable react-hooks/set-state-in-effect -- dialog-open reset: form
       fields are (re)initialized synchronously from props when the dialog opens. */
    setName(existingGoal?.name ?? '')
    setTargetAmount(existingGoal?.target_amount ?? '')
    setCurrentAmount(existingGoal?.current_amount ?? '0')
    setTargetDate(existingGoal?.target_date ?? '')
    setDescription(existingGoal?.description ?? '')
    setError(null)
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [open, existingGoal])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await onSubmit({
        name,
        target_amount: targetAmount,
        current_amount: currentAmount || '0',
        target_date: targetDate || null,
        description: description || null,
      })
    } catch {
      setError('Could not save this goal. Please check the fields and try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{existingGoal ? 'Edit' : 'New'} savings goal</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Stack spacing={2}>
            <TextField
              label="Goal name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <TextField
              label="Target amount"
              type="number"
              required
              slotProps={{ htmlInput: { step: '0.01', min: '0.01' } }}
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
            />
            <TextField
              label="Current amount saved"
              type="number"
              slotProps={{ htmlInput: { step: '0.01', min: '0' } }}
              value={currentAmount}
              onChange={(e) => setCurrentAmount(e.target.value)}
            />
            <TextField
              label="Target date"
              type="date"
              slotProps={{ inputLabel: { shrink: true } }}
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              helperText="Optional — needed to show whether you're on track"
            />
            <TextField
              label="Description"
              multiline
              minRows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
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
