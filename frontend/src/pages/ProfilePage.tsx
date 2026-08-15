import { useState } from 'react'
import type { FormEvent } from 'react'
import { Alert, Box, Button, Divider, Paper, Stack, TextField, Typography } from '@mui/material'
import { isAxiosError } from 'axios'
import * as authApi from '../api/auth'
import { useAuth } from '../hooks/useAuth'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()

  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [profileMessage, setProfileMessage] = useState<{
    type: 'success' | 'error'
    text: string
  } | null>(null)
  const [isSavingProfile, setIsSavingProfile] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordMessage, setPasswordMessage] = useState<{
    type: 'success' | 'error'
    text: string
  } | null>(null)
  const [isSavingPassword, setIsSavingPassword] = useState(false)

  if (!user) {
    return null
  }

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setProfileMessage(null)
    setIsSavingProfile(true)
    try {
      await authApi.updateProfile({ full_name: fullName })
      await refreshUser()
      setProfileMessage({ type: 'success', text: 'Profile updated.' })
    } catch {
      setProfileMessage({ type: 'error', text: 'Could not update profile. Please try again.' })
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setPasswordMessage(null)
    setIsSavingPassword(true)
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setPasswordMessage({ type: 'success', text: 'Password changed.' })
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 400) {
        setPasswordMessage({ type: 'error', text: 'Current password is incorrect.' })
      } else {
        setPasswordMessage({ type: 'error', text: 'Could not change password. Please try again.' })
      }
    } finally {
      setIsSavingPassword(false)
    }
  }

  return (
    <Box sx={{ p: 4, maxWidth: 480 }}>
      <Typography variant="h4" gutterBottom>
        Profile
      </Typography>

      <Paper component="form" onSubmit={handleProfileSubmit} elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Account details
        </Typography>
        {profileMessage && (
          <Alert severity={profileMessage.type} sx={{ mb: 2 }}>
            {profileMessage.text}
          </Alert>
        )}
        <Stack spacing={2}>
          <TextField label="Email" value={user.email} disabled fullWidth />
          <TextField
            label="Full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            fullWidth
            required
          />
          <Button
            type="submit"
            variant="contained"
            disabled={isSavingProfile}
            sx={{ alignSelf: 'start' }}
          >
            {isSavingProfile ? 'Saving…' : 'Save changes'}
          </Button>
        </Stack>
      </Paper>

      <Divider sx={{ mb: 3 }} />

      <Paper component="form" onSubmit={handlePasswordSubmit} elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Change password
        </Typography>
        {passwordMessage && (
          <Alert severity={passwordMessage.type} sx={{ mb: 2 }}>
            {passwordMessage.text}
          </Alert>
        )}
        <Stack spacing={2}>
          <TextField
            label="Current password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="New password"
            type="password"
            helperText="At least 8 characters"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            fullWidth
            required
          />
          <Button
            type="submit"
            variant="contained"
            disabled={isSavingPassword}
            sx={{ alignSelf: 'start' }}
          >
            {isSavingPassword ? 'Updating…' : 'Update password'}
          </Button>
        </Stack>
      </Paper>
    </Box>
  )
}
