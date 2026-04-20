import api from '../lib/api'

export interface AWSAccount {
  id: number
  name: string
  description?: string
  sso_region: string
  kiro_region: string
  instance_arn?: string
  identity_store_id?: string
  status: string
  last_verified?: string
  permissions?: {
    has_identity_center_access: boolean
    has_kiro_access: boolean
    errors?: string[]
  }
  sync_interval_minutes?: number
  last_synced?: string
  is_default?: boolean
  kiro_login_url?: string
  access_key_masked?: string
  created_at: string
  updated_at: string
}

export interface CreateAccountRequest {
  name: string
  description?: string
  access_key_id: string
  secret_access_key: string
  sso_region?: string
  kiro_region?: string
  sync_interval_minutes?: number
  is_default?: boolean
  kiro_login_url?: string
}

export interface AccountListResponse {
  total: number
  accounts: AWSAccount[]
}

export interface VerificationResponse {
  account_id: number
  status: string
  instance_arn?: string
  identity_store_id?: string
  permissions?: {
    has_identity_center_access: boolean
    has_kiro_access: boolean
    errors?: string[]
  }
  message?: string
}

const accountService = {
  async list(skip = 0, limit = 100): Promise<AccountListResponse> {
    const response = await api.get<AccountListResponse>('/accounts', {
      params: { skip, limit },
    })
    return response.data
  },

  async get(id: number): Promise<AWSAccount> {
    const response = await api.get<AWSAccount>(`/accounts/${id}`)
    return response.data
  },

  async create(data: CreateAccountRequest): Promise<AWSAccount> {
    const response = await api.post<AWSAccount>('/accounts', data)
    return response.data
  },

  async update(id: number, data: Partial<CreateAccountRequest>): Promise<AWSAccount> {
    const response = await api.put<AWSAccount>(`/accounts/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/accounts/${id}`)
  },

  async verify(id: number): Promise<VerificationResponse> {
    const response = await api.post<VerificationResponse>(`/accounts/${id}/verify`)
    return response.data
  },

  async sync(id: number): Promise<{ synced_users: number; synced_subscriptions: number }> {
    const response = await api.post(`/accounts/${id}/sync`)
    return response.data
  },

  async getStats(accountId?: number): Promise<{
    total_users: number
    subscribed_users: number
    active_subscriptions: number
    total_accounts: number
    active_accounts: number
  }> {
    const response = await api.get('/accounts/stats', {
      params: accountId ? { account_id: accountId } : {},
    })
    return response.data
  },
}

export { accountService }
export default accountService
