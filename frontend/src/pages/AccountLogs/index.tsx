import React from 'react';
import { Table, Card, Tag, Space, Select, DatePicker, Button, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { logService, OperationLog } from '../../services/logs';
import { useAccountStore } from '../../stores/accountStore';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const operationOptions = [
  { value: 'create_account', label: '创建账号' },
  { value: 'verify_account', label: '验证账号' },
  { value: 'sync_account_data', label: '同步数据' },
  { value: 'create_user', label: '创建用户' },
  { value: 'delete_user', label: '删除用户' },
  { value: 'create_subscription', label: '创建订阅' },
  { value: 'delete_subscription', label: '删除订阅' },
  { value: 'change_plan', label: '更改计划' },
];

const statusColors: Record<string, string> = {
  success: 'green',
  failed: 'red',
  pending: 'blue',
};

const statusText: Record<string, string> = {
  success: '成功',
  failed: '失败',
  pending: '进行中',
};

const operationText: Record<string, string> = {
  create_account: '创建账号',
  verify_account: '验证账号',
  sync_account_data: '同步数据',
  create_user: '创建用户',
  delete_user: '删除用户',
  create_subscription: '创建订阅',
  delete_subscription: '删除订阅',
  change_plan: '更改计划',
};

const AccountLogs: React.FC = () => {
  const [logs, setLogs] = React.useState<OperationLog[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [total, setTotal] = React.useState(0);
  const [pagination, setPagination] = React.useState({ current: 1, pageSize: 20 });
  const [filters, setFilters] = React.useState<{
    operation?: string;
    status?: string;
    dateRange?: [dayjs.Dayjs, dayjs.Dayjs];
  }>({});

  const { currentAccount } = useAccountStore();

  const fetchLogs = React.useCallback(async () => {
    if (!currentAccount) return;
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      };
      if (filters.operation) params.operation = filters.operation;
      if (filters.status) params.status = filters.status;
      if (filters.dateRange) {
        params.start_date = filters.dateRange[0].toISOString();
        params.end_date = filters.dateRange[1].toISOString();
      }

      const data = await logService.listLogs(currentAccount.id, params);
      setLogs(data.logs);
      setTotal(data.total);
    } catch (error) {
      message.error('获取操作日志失败');
    } finally {
      setLoading(false);
    }
  }, [currentAccount, pagination, filters]);

  React.useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleTableChange = (newPagination: { current?: number; pageSize?: number }) => {
    setPagination({
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || 20,
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '操作类型',
      dataIndex: 'operation',
      key: 'operation',
      width: 120,
      render: (operation: string) => operationText[operation] || operation,
    },
    {
      title: '操作目标',
      dataIndex: 'target',
      key: 'target',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>
          {statusText[status] || status}
        </Tag>
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: '操作人',
      dataIndex: 'operator',
      key: 'operator',
      width: 150,
      render: (operator: string | null) => operator || '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="操作日志">
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder="操作类型"
            allowClear
            style={{ width: 150 }}
            options={operationOptions}
            onChange={(value) => setFilters({ ...filters, operation: value })}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            options={[
              { value: 'success', label: '成功' },
              { value: 'failed', label: '失败' },
              { value: 'pending', label: '进行中' },
            ]}
            onChange={(value) => setFilters({ ...filters, status: value })}
          />
          <RangePicker
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setFilters({
                  ...filters,
                  dateRange: [dates[0], dates[1]] as [dayjs.Dayjs, dayjs.Dayjs],
                });
              } else {
                setFilters({ ...filters, dateRange: undefined });
              }
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  );
};

export default AccountLogs;
