import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TrendItem } from '../../types/analytics'
import {
  CHART_GRIDLINE,
  CHART_MUTED_INK,
  STATUS_CRITICAL,
  STATUS_GOOD,
} from '../../utils/chartColors'
import { formatCurrency } from '../../utils/format'

const MONTH_LABELS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
]

interface TrendChartProps {
  data: TrendItem[]
  height?: number
}

export default function TrendChart({ data, height = 260 }: TrendChartProps) {
  const chartData = data.map((item) => ({
    label: `${MONTH_LABELS[item.month - 1]} ${item.year}`,
    Income: Number(item.income),
    Expenses: Number(item.expenses),
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRIDLINE} vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: CHART_MUTED_INK, fontSize: 12 }}
          axisLine={{ stroke: CHART_GRIDLINE }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: CHART_MUTED_INK, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(value: number) => formatCurrency(String(value))}
          width={80}
        />
        <Tooltip formatter={(value) => formatCurrency(String(value))} />
        <Legend />
        <Bar dataKey="Income" fill={STATUS_GOOD} radius={[4, 4, 0, 0]} />
        <Bar dataKey="Expenses" fill={STATUS_CRITICAL} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
