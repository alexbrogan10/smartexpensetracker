import { useEffect, useState } from 'react'
import { Alert, Box, Card, CardContent, CircularProgress, Stack, Typography } from '@mui/material'
import * as predictionsApi from '../api/predictions'
import * as recommendationsApi from '../api/recommendations'
import type { Recommendation, RecommendationSeverity } from '../types/recommendation'
import type { SpendingPrediction } from '../types/prediction'
import { formatCurrency } from '../utils/format'

const SEVERITY_TO_ALERT: Record<RecommendationSeverity, 'info' | 'warning' | 'error'> = {
  info: 'info',
  warning: 'warning',
  critical: 'error',
}

function formatMonthLabel(yearMonth: string): string {
  const [year, month] = yearMonth.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })
}

export default function InsightsPage() {
  const [prediction, setPrediction] = useState<SpendingPrediction | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([predictionsApi.getSpendingPrediction(), recommendationsApi.getRecommendations()])
      .then(([predictionData, recommendationsData]) => {
        setPrediction(predictionData)
        setRecommendations(recommendationsData)
      })
      .catch(() => setError('Could not load insights. Please try again.'))
  }, [])

  if (error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  if (!prediction || !recommendations) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 4, maxWidth: 900 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Insights
      </Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>
            Spending forecast for {formatMonthLabel(prediction.next_month)}
          </Typography>

          {prediction.status === 'insufficient_data' ? (
            <Typography color="text.secondary">
              Not enough transaction history yet to forecast next month. Keep logging transactions
              and a forecast will appear here once a few months of data build up.
            </Typography>
          ) : (
            <>
              <Stack direction="row" sx={{ gap: 4, flexWrap: 'wrap', mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Predicted income
                  </Typography>
                  <Typography variant="h5">
                    {prediction.predicted_income !== null
                      ? formatCurrency(prediction.predicted_income)
                      : '—'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Predicted expenses
                  </Typography>
                  <Typography variant="h5">
                    {prediction.predicted_expenses !== null
                      ? formatCurrency(prediction.predicted_expenses)
                      : '—'}
                  </Typography>
                </Box>
              </Stack>

              {prediction.by_category.length > 0 && (
                <>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Categories trending highest
                  </Typography>
                  <Stack spacing={0.5}>
                    {prediction.by_category.map((item) => (
                      <Stack
                        key={item.category_id}
                        direction="row"
                        sx={{ justifyContent: 'space-between' }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          {item.category_name}
                        </Typography>
                        <Typography variant="body2">
                          {formatCurrency(item.predicted_amount)}
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>
            Recommendations
          </Typography>

          {recommendations.length === 0 ? (
            <Typography color="text.secondary">
              You're on track — no recommendations right now.
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {recommendations.map((rec, index) => (
                <Alert key={index} severity={SEVERITY_TO_ALERT[rec.severity]}>
                  {rec.message}
                </Alert>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
