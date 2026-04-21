import React from 'react';
import { Card, Tag, Space, Select, DatePicker, Button, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { logService, OperationLog } from '../../services/logs';
import { useAccountStore } from '../../stores/accountStore';
import ResponsiveList from '../../components/ResponsiveList';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const operationOptions = [
  { value: 'create_account' },
  { value: 'verify_account' },
  { value: 'sync_account_data' },
  { value: 'create_user' },
  { value: 'delete_user' },
  { value: 'create_subscription' },
  { value: 'delete_subscription' },
  { value: 'change_plan' },
];

const statusColors: Record<string, string> = {
  success: 'green',
  failed: 'red',
  pending: 'blue',
};

const AccountLogs: React.FC = () => {
  const { t } = useTranslation();
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
      title: t('logs.operation'),
      dataIndex: 'operation',
      key: 'operation',
      width: 120,
      render: (operation: string) => t(`logs.operations.${operation}`, { defaultValue: operation }),
    },
    {
      title: t('logs.target'),
      dataIndex: 'target',
      key: 'target',
      width: 200,
    },
    {
      title: t('common.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>
          {t(`logs.statuses.${status}`, { defaultValue: status })}
        </Tag>
      ),
    },
    {
      title: t('logs.message'),
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: t('logs.operator'),
      dataIndex: 'operator',
      key: 'operator',
      width: 150,
      render: (operator: string | null) => operator || '-',
    },
    {
      title: t('logs.time'),
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title={t('logs.title')}>
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder={t('logs.filterOperation')}
            allowClear
            style={{ width: 150 }}
            options={operationOptions.map(o => ({ value: o.value, label: t(`logs.operations.${o.value}`, { defaultValue: o.value }) }))}
            onChange={(value) => setFilters({ ...filters, operation: value })}
          />
          <Select
            placeholder={t('logs.filterStatus')}
            allowClear
            style={{ width: 120 }}
            options={[
              { value: 'success', label: t('logs.statuses.success') },
              { value: 'failed', label: t('logs.statuses.failed') },
              { value: 'pending', label: t('logs.statuses.pending') },
            ]}
            onChange={(value) => setFilters({ ...filters, status: value })}
          />
          <RangePicker
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setFilters({ ...filters, dateRange: [dates[0], dates[1]] as [dayjs.Dayjs, dayjs.Dayjs] });
              } else {
                setFilters({ ...filters, dateRange: undefined });
              }
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchLogs}>{t('common.refresh')}</Button>
        </Space>

        <ResponsiveList
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total,
            showTotal: (n: number) => t('common.total', { count: n }),
            onChange: (page: number, pageSize: number) => handleTableChange({ current: page, pageSize }),
          }}
        />
      </Card>
    </div>
  );
};

export default AccountLogs;
