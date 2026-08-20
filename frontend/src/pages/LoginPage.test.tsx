import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import { AuthProvider } from '../features/auth/AuthContext'
import * as authApi from '../api/auth'
import { clearToken } from '../utils/tokenStorage'

vi.mock('../api/auth')

const mockedAuthApi = vi.mocked(authApi)

const FAKE_USER = {
  id: 'user-1',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<div>Home Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function fillAndSubmit(email: string, password: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/email/i), email)
  await user.type(screen.getByLabelText(/password/i), password)
  await user.click(screen.getByRole('button', { name: /sign in/i }))
}

describe('LoginPage', () => {
  beforeEach(() => {
    clearToken()
    vi.clearAllMocks()
  })

  it('renders the sign-in form', () => {
    renderLoginPage()

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('navigates to the home page after a successful login', async () => {
    mockedAuthApi.login.mockResolvedValue({ access_token: 'fake-token', token_type: 'bearer' })
    mockedAuthApi.getCurrentUser.mockResolvedValue(FAKE_USER)

    renderLoginPage()
    await fillAndSubmit('jane@example.com', 'password123')

    await waitFor(() => expect(screen.getByText('Home Page')).toBeInTheDocument())
    expect(mockedAuthApi.login).toHaveBeenCalledWith({
      email: 'jane@example.com',
      password: 'password123',
    })
  })

  it('shows an error message and stays on the page when login fails', async () => {
    mockedAuthApi.login.mockRejectedValue(new Error('invalid credentials'))

    renderLoginPage()
    await fillAndSubmit('jane@example.com', 'wrong-password')

    expect(await screen.findByText('Incorrect email or password.')).toBeInTheDocument()
    expect(screen.queryByText('Home Page')).not.toBeInTheDocument()
  })
})
