import type {
  PaginatedResponse,
  Transaction,
  TransactionFilters,
  TransactionInput,
} from '../types/transaction'
import { apiClient } from './client'

export async function listTransactions(
  filters: TransactionFilters,
): Promise<PaginatedResponse<Transaction>> {
  const response = await apiClient.get<PaginatedResponse<Transaction>>('/transactions', {
    params: filters,
  })
  return response.data
}

export async function getTransaction(id: string): Promise<Transaction> {
  const response = await apiClient.get<Transaction>(`/transactions/${id}`)
  return response.data
}

export async function createTransaction(data: TransactionInput): Promise<Transaction> {
  const response = await apiClient.post<Transaction>('/transactions', data)
  return response.data
}

export async function updateTransaction(
  id: string,
  data: Partial<TransactionInput>,
): Promise<Transaction> {
  const response = await apiClient.put<Transaction>(`/transactions/${id}`, data)
  return response.data
}

export async function deleteTransaction(id: string): Promise<void> {
  await apiClient.delete(`/transactions/${id}`)
}
