import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from './AuthContext'
import { useAuth } from '../../hooks/useAuth'
import * as authApi from '../../api/auth'
import { clearToken } from '../../utils/tokenStorage'

vi.mock('../../api/auth')

const mockedAuthApi = vi.mocked(authApi)

const FAKE_USER = {
  id: 'user-1',
  email: 'jane@example.com',
  full_name: 'Jane Doe',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

function AuthProbe() {
  const { user, isAuthenticated, login, logout } = useAuth()
  return (
    <div>
      <div data-testid="status">{isAuthenticated ? 'authenticated' : 'anonymous'}</div>
      <div data-testid="name">{user?.full_name ?? 'none'}</div>
      <button onClick={() => login({ email: 'jane@example.com', password: 'password123' })}>
        log in
      </button>
      <button onClick={logout}>log out</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    clearToken()
    vi.clearAllMocks()
  })

  it('starts unauthenticated with no stored token', () => {
    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
  })

  it('becomes authenticated after a successful login', async () => {
    mockedAuthApi.login.mockResolvedValue({ access_token: 'fake-token', token_type: 'bearer' })
    mockedAuthApi.getCurrentUser.mockResolvedValue(FAKE_USER)
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await user.click(screen.getByText('log in'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    expect(screen.getByTestId('name')).toHaveTextContent('Jane Doe')
  })

  it('clears user state on logout', async () => {
    mockedAuthApi.login.mockResolvedValue({ access_token: 'fake-token', token_type: 'bearer' })
    mockedAuthApi.getCurrentUser.mockResolvedValue(FAKE_USER)
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>,
    )

    await user.click(screen.getByText('log in'))
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))

    await user.click(screen.getByText('log out'))

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('name')).toHaveTextContent('none')
  })
})
