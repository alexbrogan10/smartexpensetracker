import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CategoryBreakdownItem } from '../../types/analytics'
import { CATEGORICAL_PALETTE } from '../../utils/chartColors'
import { formatCurrency } from '../../utils/format'

interface CategoryPieChartProps {
  data: CategoryBreakdownItem[]
  height?: number
}

const MAX_SLICES = CATEGORICAL_PALETTE.length

export default function CategoryPieChart({ data, height = 280 }: CategoryPieChartProps) {
  const shown = data.slice(0, MAX_SLICES - (data.length > MAX_SLICES ? 1 : 0))
  const overflow = data.slice(shown.length)

  const chartData = shown.map((item) => ({
    name: item.category.name,
    value: Number(item.amount),
  }))
  if (overflow.length > 0) {
    chartData.push({
      name: 'Other',
      value: overflow.reduce((sum, item) => sum + Number(item.amount), 0),
    })
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          innerRadius="55%"
          outerRadius="80%"
          paddingAngle={2}
        >
          {chartData.map((entry, index) => (
            <Cell key={entry.name} fill={CATEGORICAL_PALETTE[index % CATEGORICAL_PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => formatCurrency(String(value))} />
        <Legend layout="vertical" align="right" verticalAlign="middle" />
      </PieChart>
    </ResponsiveContainer>
  )
}
