import type { TransactionFilters } from '../types/transaction'
import { apiClient } from './client'

export type ExportFormat = 'csv' | 'xlsx'

type ExportFilters = Pick<
  TransactionFilters,
  | 'type'
  | 'category_id'
  | 'date_from'
  | 'date_to'
  | 'min_amount'
  | 'max_amount'
  | 'is_recurring'
  | 'payment_method'
  | 'search'
>

function filenameFromContentDisposition(header: string | undefined, fallback: string): string {
  const match = header?.match(/filename="?([^"]+)"?/)
  return match ? match[1] : fallback
}

export async function exportTransactions(
  format: ExportFormat,
  filters: ExportFilters,
): Promise<void> {
  const response = await apiClient.get('/reports/export', {
    params: { format, ...filters },
    responseType: 'blob',
  })

  const filename = filenameFromContentDisposition(
    response.headers['content-disposition'],
    `transactions.${format}`,
  )

  const url = URL.createObjectURL(response.data as Blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
