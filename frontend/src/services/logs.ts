import api from '../lib/api';

export interface OperationLog {
  id: number;
  aws_account_id: number;
  operation: string;
  target: string;
  status: string;
  message: string | null;
  details: Record<string, unknown> | null;
  operator: string | null;
  created_at: string;
}

export interface OperationLogListResponse {
  total: number;
  logs: OperationLog[];
}

export const logService = {
  async listLogs(
    accountId: number,
    params?: {
      skip?: number;
      limit?: number;
      operation?: string;
      status?: string;
      startDate?: string;
      endDate?: string;
    }
  ): Promise<OperationLogListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.operation) queryParams.append('operation', params.operation);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.startDate) queryParams.append('start_date', params.startDate);
    if (params?.endDate) queryParams.append('end_date', params.endDate);

    const response = await api.get(
      `/accounts/${accountId}/logs?${queryParams.toString()}`
    );
    return response.data;
  },

  async getLog(accountId: number, logId: number): Promise<OperationLog> {
    const response = await api.get(`/accounts/${accountId}/logs/${logId}`);
    return response.data;
  },
};
