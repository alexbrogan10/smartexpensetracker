import { apiClient } from './client'
import type {
  AuthToken,
  ChangePasswordRequest,
  LoginRequest,
  RegisterRequest,
  UpdateProfileRequest,
  User,
} from '../types/user'

export async function register(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data)
  return response.data
}

export async function login(data: LoginRequest): Promise<AuthToken> {
  // The backend's /auth/login uses the standard OAuth2 form body
  // (username/password) rather than JSON, so Swagger's "Authorize" flow
  // works out of the box against the same endpoint.
  const form = new URLSearchParams()
  form.set('username', data.email)
  form.set('password', data.password)

  const response = await apiClient.post<AuthToken>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/users/me')
  return response.data
}

export async function updateProfile(data: UpdateProfileRequest): Promise<User> {
  const response = await apiClient.put<User>('/users/me', data)
  return response.data
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await apiClient.post('/users/me/change-password', data)
}
