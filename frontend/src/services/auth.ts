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
  is_admin: boolean
  mfa_enabled: boolean
}

class MfaRequiredError {
  mfa_required = true
  user_id: number
  constructor(userId: number) {
    this.user_id = userId
  }
}

const authService = {
  async login(username: string, password: string): Promise<boolean | 'mfa_required'> {
    try {
      // 直接用 axios 避免 interceptor 干扰
      const response = await api.post('/auth/login', { username, password })
      const data = response.data

      if (data.mfa_required) {
        throw new MfaRequiredError(data.user_id)
      }

      const { access_token, refresh_token } = data
      const userResponse = await api.get<CurrentUser>('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      })
      useAuthStore.getState().login(access_token, refresh_token, userResponse.data)
      localStorage.setItem('refresh_token', refresh_token)
      return true
    } catch (error: any) {
      if (error instanceof MfaRequiredError || error?.mfa_required) {
        throw error
      }
      console.error('Login failed:', error)
      return false
    }
  },

  async loginWithMfa(userId: number, code: string): Promise<boolean> {
    try {
      const response = await api.post<TokenResponse>('/auth/login/mfa', {
        user_id: userId,
        code,
      })
      const { access_token, refresh_token } = response.data
      const userResponse = await api.get<CurrentUser>('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      })
      useAuthStore.getState().login(access_token, refresh_token, userResponse.data)
      localStorage.setItem('refresh_token', refresh_token)
      return true
    } catch {
      return false
    }
  },

  async refresh(): Promise<TokenResponse> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) throw new Error('No refresh token')
    const response = await api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
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
    try { await api.post('/auth/logout') } finally {
      useAuthStore.getState().logout()
      localStorage.removeItem('refresh_token')
    }
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      await api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword })
      return true
    } catch { return false }
  },

  async setupMfa(): Promise<{ secret: string; uri: string; qr_code: string }> {
    const response = await api.post('/auth/mfa/setup')
    return response.data
  },

  async verifyMfa(code: string): Promise<boolean> {
    try {
      await api.post('/auth/mfa/verify', { code })
      return true
    } catch { return false }
  },

  async disableMfa(): Promise<boolean> {
    try {
      await api.post('/auth/mfa/disable')
      return true
    } catch { return false }
  },
}

export default authService
