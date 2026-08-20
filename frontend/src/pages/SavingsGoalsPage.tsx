import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import * as savingsGoalsApi from '../api/savingsGoals'
import ConfirmDialog from '../components/ConfirmDialog'
import SavingsGoalFormDialog from '../components/SavingsGoalFormDialog'
import { useToast } from '../hooks/useToast'
import type { SavingsGoal, SavingsGoalInput } from '../types/savingsGoal'
import { formatCurrency, formatDate } from '../utils/format'

export default function SavingsGoalsPage() {
  const { showSuccess, showError } = useToast()
  const [goals, setGoals] = useState<SavingsGoal[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [editingGoal, setEditingGoal] = useState<SavingsGoal | null>(null)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const load = () => {
    setIsLoading(true)
    setError(null)
    savingsGoalsApi
      .listSavingsGoals()
      .then(setGoals)
      .catch(() => setError('Could not load savings goals. Please try again.'))
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch-on-mount: results land in the promise resolution, not synchronously here.
    load()
  }, [])

  const openCreateForm = () => {
    setEditingGoal(null)
    setIsFormOpen(true)
  }

  const openEditForm = (goal: SavingsGoal) => {
    setEditingGoal(goal)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (data: SavingsGoalInput) => {
    if (editingGoal) {
      await savingsGoalsApi.updateSavingsGoal(editingGoal.id, data)
      showSuccess('Savings goal updated.')
    } else {
      await savingsGoalsApi.createSavingsGoal(data)
      showSuccess('Savings goal created.')
    }
    setIsFormOpen(false)
    load()
  }

  const handleConfirmDelete = async () => {
    if (!pendingDeleteId) return
    setIsDeleting(true)
    try {
      await savingsGoalsApi.deleteSavingsGoal(pendingDeleteId)
      setPendingDeleteId(null)
      load()
      showSuccess('Savings goal deleted.')
    } catch {
      showError('Could not delete this goal. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 720 }}>
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Savings goals</Typography>
        <Button variant="contained" onClick={openCreateForm}>
          Add goal
        </Button>
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

      {!isLoading && goals.length === 0 && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography color="text.secondary">No savings goals yet.</Typography>
          </CardContent>
        </Card>
      )}

      <Stack spacing={2}>
        {goals.map((goal) => (
          <Card key={goal.id} variant="outlined">
            <CardContent>
              <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'start' }}>
                <Box>
                  <Stack direction="row" sx={{ alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="subtitle1">{goal.name}</Typography>
                    {goal.is_on_track !== null && (
                      <Chip
                        size="small"
                        label={goal.is_on_track ? 'On track' : 'Behind'}
                        color={goal.is_on_track ? 'success' : 'warning'}
                      />
                    )}
                  </Stack>
                  {goal.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {goal.description}
                    </Typography>
                  )}
                </Box>
                <Stack direction="row">
                  <IconButton size="small" aria-label="edit" onClick={() => openEditForm(goal)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    aria-label="delete"
                    onClick={() => setPendingDeleteId(goal.id)}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Stack>
              </Stack>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
                {goal.target_date && ` · by ${formatDate(goal.target_date)}`}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={goal.progress_percentage}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary">
                {goal.progress_percentage}% complete
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <SavingsGoalFormDialog
        open={isFormOpen}
        existingGoal={editingGoal}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
      />

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="Delete savings goal?"
        message="This action cannot be undone."
        isConfirming={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setPendingDeleteId(null)}
      />
    </Box>
  )
}
