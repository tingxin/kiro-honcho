import api from '../lib/api';

export interface User {
  id: number;
  user_id: string;
  user_name: string;
  display_name: string | null;
  email: string;
  given_name: string | null;
  family_name: string | null;
  status: string;
  groups: Record<string, unknown>[] | null;
  has_subscription: boolean;
  subscription_type: string | null;
  last_synced: string | null;
  created_at: string;
}

export interface UserListResponse {
  total: number;
  users: User[];
}

export interface CreateUserRequest {
  email: string;
  given_name: string;
  family_name: string;
  display_name?: string;
  user_name?: string;
  auto_subscribe?: boolean;
  subscription_type?: string;
  send_password_reset?: boolean;
}

export const userService = {
  async listUsers(accountId: number, skip = 0, limit = 100, search?: string): Promise<UserListResponse> {
    const response = await api.get<UserListResponse>(`/accounts/${accountId}/users`, {
      params: { skip, limit, search },
    });
    return response.data;
  },

  async createUser(accountId: number, data: CreateUserRequest): Promise<User> {
    const response = await api.post<User>(`/accounts/${accountId}/users`, data);
    return response.data;
  },

  async getUser(accountId: number, userId: number): Promise<User> {
    const response = await api.get<User>(`/accounts/${accountId}/users/${userId}`);
    return response.data;
  },

  async deleteUser(accountId: number, userId: number): Promise<void> {
    await api.delete(`/accounts/${accountId}/users/${userId}`);
  },

  async resetPassword(accountId: number, userId: number, mode: 'email' | 'otp' = 'email'): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/accounts/${accountId}/users/${userId}/reset-password`, { mode });
    return response.data;
  },

  async sendVerificationEmail(accountId: number, userId: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/accounts/${accountId}/users/${userId}/verify-email`);
    return response.data;
  },
};
