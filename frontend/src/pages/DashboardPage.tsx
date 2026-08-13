import { Box, Typography } from '@mui/material'

export default function DashboardPage() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Smart Expense Tracker
      </Typography>
      <Typography color="text.secondary">
        Project scaffold is up and running. The dashboard will be built in a later milestone.
      </Typography>
    </Box>
  )
}
