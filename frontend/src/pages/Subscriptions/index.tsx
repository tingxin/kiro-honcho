import React from 'react';
import { Table, Button, Space, Tag, Modal, Form, Select, message, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import styles from './Subscriptions.module.css';
import { subscriptionService, Subscription } from '../../services/subscriptions';
import { useAccountStore } from '../../stores/accountStore';

const planLabels: Record<string, string> = {
  Q_DEVELOPER_STANDALONE_PRO: 'Q Developer Pro',
  Q_DEVELOPER_STANDALONE_PRO_PLUS: 'Q Developer Pro+',
  Q_DEVELOPER_STANDALONE_PRO_POWER: 'Q Developer Pro Power',
};

const Subscriptions: React.FC = () => {
  const [subscriptions, setSubscriptions] = React.useState<Subscription[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [total, setTotal] = React.useState(0);
  const [changePlanModalVisible, setChangePlanModalVisible] = React.useState(false);
  const [selectedSubscription, setSelectedSubscription] = React.useState<Subscription | null>(null);
  const [form] = Form.useForm();

  const { currentAccount } = useAccountStore();

  const fetchSubscriptions = React.useCallback(async () => {
    if (!currentAccount) return;
    setLoading(true);
    try {
      const response = await subscriptionService.list(currentAccount.id);
      setSubscriptions(response.subscriptions || []);
      setTotal(response.total || 0);
    } catch (error) {
      message.error('获取订阅列表失败');
    } finally {
      setLoading(false);
    }
  }, [currentAccount]);

  React.useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const handleChangePlan = async (values: { subscription_type: string }) => {
    if (!currentAccount || !selectedSubscription) return;
    try {
      await subscriptionService.update(currentAccount.id, selectedSubscription.id, values.subscription_type);
      message.success('套餐变更成功');
      setChangePlanModalVisible(false);
      form.resetFields();
      fetchSubscriptions();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '套餐变更失败');
    }
  };

  const handleDeleteSubscription = async (subscriptionId: number) => {
    if (!currentAccount) return;
    try {
      await subscriptionService.delete(currentAccount.id, subscriptionId);
      message.success('订阅已取消');
      fetchSubscriptions();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消订阅失败');
    }
  };

  const columns = [
    {
      title: '用户邮箱',
      dataIndex: 'user_email',
      key: 'user_email',
      render: (email: string | null) => email || '-',
    },
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      render: (name: string | null) => name || '-',
    },
    {
      title: '当前套餐',
      dataIndex: 'subscription_type',
      key: 'subscription_type',
      render: (type: string) => (
        <Tag color="blue">{planLabels[type] || type}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '已激活' : status}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: Subscription) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => {
              setSelectedSubscription(record);
              form.setFieldsValue({ subscription_type: record.subscription_type });
              setChangePlanModalVisible(true);
            }}
          >
            变更套餐
          </Button>
          <Popconfirm
            title="确定取消该订阅？"
            onConfirm={() => handleDeleteSubscription(record.id)}
          >
            <Button type="link" size="small" danger>
              取消订阅
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className={styles.subscriptions}>
      <div className={styles.header}>
        <h2>订阅管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchSubscriptions}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} disabled>
            添加订阅
          </Button>
        </Space>
      </div>

      <Table
        className={styles.table}
        columns={columns}
        dataSource={subscriptions}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: 100, showTotal: (t) => `共 ${t} 个订阅` }}
      />

      <Modal
        title="变更套餐"
        open={changePlanModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setChangePlanModalVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} onFinish={handleChangePlan} layout="vertical">
          <p style={{ marginBottom: 16 }}>
            当前用户: {selectedSubscription?.user_email || selectedSubscription?.principal_id}
          </p>
          <Form.Item name="subscription_type" label="套餐类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Q Developer Pro</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Q Developer Pro+</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_POWER">Q Developer Pro Power</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Subscriptions;
