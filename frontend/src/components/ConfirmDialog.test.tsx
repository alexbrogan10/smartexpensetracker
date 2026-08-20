import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import ConfirmDialog from './ConfirmDialog'

describe('ConfirmDialog', () => {
  it('renders nothing visible when closed', () => {
    render(
      <ConfirmDialog
        open={false}
        title="Delete item?"
        message="This cannot be undone."
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )

    expect(screen.queryByText('Delete item?')).not.toBeInTheDocument()
  })

  it('renders the title and message when open', () => {
    render(
      <ConfirmDialog
        open
        title="Delete item?"
        message="This cannot be undone."
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )

    expect(screen.getByText('Delete item?')).toBeInTheDocument()
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument()
  })

  it('calls onConfirm when the confirm button is clicked', async () => {
    const onConfirm = vi.fn()
    const user = userEvent.setup()
    render(
      <ConfirmDialog
        open
        title="Delete item?"
        message="This cannot be undone."
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    )

    await user.click(screen.getByText('Delete'))

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onCancel when the cancel button is clicked', async () => {
    const onCancel = vi.fn()
    const user = userEvent.setup()
    render(
      <ConfirmDialog
        open
        title="Delete item?"
        message="This cannot be undone."
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    )

    await user.click(screen.getByText('Cancel'))

    expect(onCancel).toHaveBeenCalledTimes(1)
  })

  it('disables both buttons and shows a busy label while confirming', () => {
    render(
      <ConfirmDialog
        open
        title="Delete item?"
        message="This cannot be undone."
        isConfirming
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )

    expect(screen.getByText('Deleting…')).toBeInTheDocument()
    expect(screen.getByText('Deleting…').closest('button')).toBeDisabled()
    expect(screen.getByText('Cancel').closest('button')).toBeDisabled()
  })

  it('uses a custom confirm label when provided', () => {
    render(
      <ConfirmDialog
        open
        title="Cancel import?"
        message="The pending import will be discarded."
        confirmLabel="Discard"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )

    expect(screen.getByText('Discard')).toBeInTheDocument()
  })
})
