import api from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface CurrentUser {
  id: number
  username: string
  email?: string
  is_active: boolean
}

const authService = {
  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await api.post<TokenResponse>('/auth/login', {
        username,
        password,
      })
      const { access_token, refresh_token } = response.data

      // Get current user info
      const userResponse = await api.get<CurrentUser>('/auth/me', {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      })

      // Store tokens and set authenticated
      useAuthStore.getState().login(access_token, refresh_token, userResponse.data)
      localStorage.setItem('refresh_token', refresh_token)

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  },

  async refresh(): Promise<TokenResponse> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token')
    }

    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })

    const { access_token, refresh_token } = response.data
    useAuthStore.getState().setTokens(access_token, refresh_token)
    localStorage.setItem('refresh_token', refresh_token)

    return response.data
  },

  async getCurrentUser(): Promise<CurrentUser> {
    const response = await api.get<CurrentUser>('/auth/me')
    return response.data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout')
    } finally {
      useAuthStore.getState().logout()
      localStorage.removeItem('refresh_token')
    }
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      return true
    } catch (error) {
      console.error('Change password failed:', error)
      return false
    }
  },
}

export default authService
