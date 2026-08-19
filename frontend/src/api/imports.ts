import type { ImportConfirmResult, ImportPreview } from '../types/transactionImport'
import { apiClient } from './client'

export async function uploadImport(file: File): Promise<ImportPreview> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<ImportPreview>('/imports/transactions', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function confirmImport(
  importId: string,
  includeDuplicates: boolean,
): Promise<ImportConfirmResult> {
  const response = await apiClient.post<ImportConfirmResult>(
    `/imports/transactions/${importId}/confirm`,
    { include_duplicates: includeDuplicates },
  )
  return response.data
}

export async function cancelImport(importId: string): Promise<void> {
  await apiClient.delete(`/imports/transactions/${importId}`)
}
