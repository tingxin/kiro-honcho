import api from '../lib/api';

export interface User {
  userId: string;
  userName: string;
  displayName: string;
  email: string;
  status: string;
  groups?: string[];
}

export interface CreateUserRequest {
  userName: string;
  displayName: string;
  email: string;
}

export const userService = {
  async listUsers(accountId: number): Promise<User[]> {
    const response = await api.get(`/api/accounts/${accountId}/users`);
    return response.data;
  },

  async createUser(accountId: number, data: CreateUserRequest): Promise<User> {
    const response = await api.post(`/api/accounts/${accountId}/users`, data);
    return response.data;
  },

  async getUser(accountId: number, userId: string): Promise<User> {
    const response = await api.get(`/api/accounts/${accountId}/users/${userId}`);
    return response.data;
  },

  async deleteUser(_accountId: number, userId: string): Promise<void> {
    await api.delete(`/api/accounts/${_accountId}/users/${userId}`);
  },

  async resetPassword(accountId: number, userId: string): Promise<void> {
    await api.post(`/api/accounts/${accountId}/users/${userId}/reset-password`);
  },

  async sendVerificationEmail(accountId: number, userId: string): Promise<void> {
    await api.post(`/api/accounts/${accountId}/users/${userId}/verify-email`);
  },
};
