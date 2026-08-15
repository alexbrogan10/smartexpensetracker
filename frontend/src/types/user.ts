export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface UpdateProfileRequest {
  full_name: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface AuthToken {
  access_token: string
  token_type: string
}
