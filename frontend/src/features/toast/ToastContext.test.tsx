import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { ToastProvider } from './ToastContext'
import { useToast } from '../../hooks/useToast'

function ToastTrigger() {
  const { showSuccess, showError } = useToast()
  return (
    <>
      <button onClick={() => showSuccess('Saved successfully.')}>trigger success</button>
      <button onClick={() => showError('Something went wrong.')}>trigger error</button>
    </>
  )
}

function renderWithProvider() {
  return render(
    <ToastProvider>
      <ToastTrigger />
    </ToastProvider>,
  )
}

describe('ToastProvider', () => {
  it('renders no toast before anything is triggered', () => {
    renderWithProvider()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows a success toast with the given message', async () => {
    const user = userEvent.setup()
    renderWithProvider()

    await user.click(screen.getByText('trigger success'))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Saved successfully.')
    expect(alert.className).toMatch(/MuiAlert-colorSuccess/)
  })

  it('shows an error toast with the given message', async () => {
    const user = userEvent.setup()
    renderWithProvider()

    await user.click(screen.getByText('trigger error'))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Something went wrong.')
    expect(alert.className).toMatch(/MuiAlert-colorError/)
  })

  it('queues a second toast while the first is still showing', async () => {
    const user = userEvent.setup()
    renderWithProvider()

    await user.click(screen.getByText('trigger success'))
    await user.click(screen.getByText('trigger error'))

    // Only the first message is visible immediately - the second waits in
    // the queue until the first's exit transition completes.
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Saved successfully.')
  })
})
