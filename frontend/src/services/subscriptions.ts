import api from '../lib/api'

export interface Subscription {
  id: number
  principal_id: string
  subscription_type: string
  status: string
  start_date?: string
  last_synced?: string
  created_at: string
  user_email?: string
  user_name?: string
  user_display_name?: string
  account_id?: number
  account_name?: string
}

export interface CreateSubscriptionRequest {
  principal_id: string
  principal_type?: string
  subscription_type?: string
}

export interface SubscriptionListResponse {
  total: number
  subscriptions: Subscription[]
}

export interface ChangePlanResult {
  email: string
  success: boolean
  message: string
}

export interface ChangePlanResponse {
  total: number
  success_count: number
  failed_count: number
  results: ChangePlanResult[]
}

const subscriptionService = {
  async list(
    accountId: number,
    skip = 0,
    limit = 100,
    subscriptionType?: string
  ): Promise<SubscriptionListResponse> {
    const response = await api.get<SubscriptionListResponse>(
      `/accounts/${accountId}/subscriptions`,
      {
        params: { skip, limit, subscription_type: subscriptionType },
      }
    )
    return response.data
  },

  async create(
    accountId: number,
    data: CreateSubscriptionRequest
  ): Promise<Subscription> {
    const response = await api.post<Subscription>(
      `/accounts/${accountId}/subscriptions`,
      data
    )
    return response.data
  },

  async update(
    accountId: number,
    subscriptionId: number,
    subscriptionType: string
  ): Promise<Subscription> {
    const response = await api.put<Subscription>(
      `/accounts/${accountId}/subscriptions/${subscriptionId}`,
      { subscription_type: subscriptionType }
    )
    return response.data
  },

  async delete(accountId: number, subscriptionId: number): Promise<void> {
    await api.delete(`/accounts/${accountId}/subscriptions/${subscriptionId}`)
  },

  async listAll(
    skip = 0,
    limit = 200,
    accountId?: number,
    subscriptionType?: string
  ): Promise<SubscriptionListResponse> {
    const response = await api.get<SubscriptionListResponse>('/subscriptions', {
      params: {
        skip, limit,
        account_id: accountId,
        subscription_type: subscriptionType,
      },
    })
    return response.data
  },

  async batchChangePlan(
    accountId: number,
    emails: string[],
    subscriptionType: string
  ): Promise<ChangePlanResponse> {
    const response = await api.post<ChangePlanResponse>(
      `/accounts/${accountId}/subscriptions/change-plan`,
      {
        emails,
        subscription_type: subscriptionType,
      }
    )
    return response.data
  },

  async listCanceled(): Promise<{
    total: number
    subscriptions: Array<{
      account_id: number
      account_name: string
      principal_id: string
      subscription_type: string
      status: string
      user_email: string | null
      user_name: string | null
    }>
  }> {
    const response = await api.get('/canceled-subscriptions')
    return response.data
  },
}

export { subscriptionService }
export default subscriptionService
