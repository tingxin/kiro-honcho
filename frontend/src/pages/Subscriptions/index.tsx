import React from 'react';
import { Button, Space, Tag, Modal, Form, Select, message, Popconfirm, Tabs, Card, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './Subscriptions.module.css';
import { subscriptionService, Subscription } from '../../services/subscriptions';
import { accountService, AWSAccount } from '../../services/accounts';
import ResponsiveList from '../../components/ResponsiveList';

const { Text } = Typography;

const planLabels: Record<string, string> = {
  Q_DEVELOPER_STANDALONE_PRO: 'Kiro Pro',
  Q_DEVELOPER_STANDALONE_PRO_PLUS: 'Kiro Pro+',
  Q_DEVELOPER_STANDALONE_POWER: 'Kiro Power',
  KIRO_ENTERPRISE_PRO: 'Kiro Pro',
  KIRO_ENTERPRISE_PRO_PLUS: 'Kiro Pro+',
  KIRO_ENTERPRISE_PRO_POWER: 'Kiro Power',
};

// ========== 活跃订阅 Tab ==========
const ActiveSubscriptions: React.FC<{ accountId: number; account: AWSAccount | null }> = ({ accountId, account }) => {
  const [subscriptions, setSubscriptions] = React.useState<Subscription[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [total, setTotal] = React.useState(0);
  const [changePlanModalVisible, setChangePlanModalVisible] = React.useState(false);
  const [selectedSubscription, setSelectedSubscription] = React.useState<Subscription | null>(null);
  const [form] = Form.useForm();

  const fetchSubscriptions = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await subscriptionService.list(accountId);
      setSubscriptions(response.subscriptions || []);
      setTotal(response.total || 0);
    } catch (error) {
      message.error('获取订阅列表失败');
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  React.useEffect(() => { fetchSubscriptions(); }, [fetchSubscriptions]);

  const handleChangePlan = async (values: { subscription_type: string }) => {
    if (!selectedSubscription) return;
    try {
      await subscriptionService.update(accountId, selectedSubscription.id, values.subscription_type);
      message.success('套餐变更成功');
      setChangePlanModalVisible(false);
      form.resetFields();
      fetchSubscriptions();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '套餐变更失败');
    }
  };

  const handleDelete = async (subscriptionId: number) => {
    try {
      await subscriptionService.delete(accountId, subscriptionId);
      message.success('订阅已取消');
      fetchSubscriptions();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消订阅失败');
    }
  };

  const columns = [
    { title: '用户邮箱', dataIndex: 'user_email', key: 'user_email', render: (v: string | null) => v || '-' },
    { title: '用户名', dataIndex: 'user_name', key: 'user_name', width: 120, render: (v: string | null) => v || '-' },
    {
      title: '套餐', dataIndex: 'subscription_type', key: 'subscription_type', width: 140,
      render: (type: string) => <Tag color="geekblue">{planLabels[type] || type}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (status: string) => {
        const upper = status?.toUpperCase();
        if (upper === 'ACTIVE') return <Tag color="green">已激活</Tag>;
        if (upper === 'PENDING') return <Tag color="orange">待激活</Tag>;
        return <Tag>{status}</Tag>;
      },
    },
    {
      title: '操作', key: 'actions', width: 180,
      render: (_: unknown, record: Subscription) => (
        <Space>
          <Button type="link" size="small" onClick={() => {
            setSelectedSubscription(record);
            form.setFieldsValue({ subscription_type: record.subscription_type });
            setChangePlanModalVisible(true);
          }}>变更套餐</Button>
          <Popconfirm title="确定取消该订阅？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger>取消订阅</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Text strong>当前账号:</Text>
          <Tag color="blue">{account?.name || '加载中...'}</Tag>
        </Space>
        <Button icon={<ReloadOutlined />} onClick={fetchSubscriptions}>刷新</Button>
      </div>
      <ResponsiveList columns={columns} dataSource={subscriptions} rowKey="id" loading={loading}
        pagination={{ total, pageSize: 100, showTotal: (t: number) => `共 ${t} 个订阅` }} />
      <Modal title="变更套餐" open={changePlanModalVisible} onOk={() => form.submit()}
        onCancel={() => { setChangePlanModalVisible(false); form.resetFields(); }}>
        <Form form={form} onFinish={handleChangePlan} layout="vertical">
          <p style={{ marginBottom: 16 }}>当前用户: {selectedSubscription?.user_email || selectedSubscription?.principal_id}</p>
          <Form.Item name="subscription_type" label="套餐类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Kiro Pro</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Kiro Pro+</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_POWER">Kiro Power</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

// ========== 已取消订阅 Tab（跨账号） ==========
interface CanceledSub {
  account_id: number;
  account_name: string;
  principal_id: string;
  subscription_type: string;
  status: string;
  user_email: string | null;
  user_name: string | null;
}

const CanceledSubscriptions: React.FC = () => {
  const [subs, setSubs] = React.useState<CanceledSub[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetch = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await subscriptionService.listCanceled();
      setSubs(data.subscriptions);
    } catch (error) {
      message.error('获取已取消订阅失败');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { fetch(); }, [fetch]);

  const columns = [
    { title: 'AWS 账号', dataIndex: 'account_name', key: 'account_name', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '用户邮箱', dataIndex: 'user_email', key: 'user_email', render: (v: string | null) => v || '-' },
    { title: '用户名', dataIndex: 'user_name', key: 'user_name', render: (v: string | null) => v || '-' },
    {
      title: '套餐', dataIndex: 'subscription_type', key: 'subscription_type',
      render: (type: string) => <Tag>{planLabels[type] || type}</Tag>,
    },
    {
      title: '状态', key: 'status', render: (_: unknown, r: CanceledSub) => {
        if (r.status === 'Orphaned') return <Tag color="orange">用户已删除</Tag>;
        return <Tag color="red">已取消</Tag>;
      }
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button icon={<ReloadOutlined />} onClick={fetch}>刷新</Button>
      </div>
      <ResponsiveList columns={columns} dataSource={subs} rowKey="principal_id" loading={loading}
        pagination={{ pageSize: 100, showTotal: (t: number) => `共 ${t} 条` }} />
    </>
  );
};

// ========== 主页面 ==========
const Subscriptions: React.FC = () => {
  const { accountId: accountIdStr } = useParams<{ accountId: string }>();
  const navigate = useNavigate();
  const accountId = Number(accountIdStr);
  const [account, setAccount] = React.useState<AWSAccount | null>(null);

  React.useEffect(() => {
    if (!accountId || isNaN(accountId)) {
      navigate('/accounts');
      return;
    }
    accountService.get(accountId).then(setAccount).catch(() => navigate('/accounts'));
  }, [accountId, navigate]);

  return (
    <div className={styles.subscriptions}>
      <Card>
        <Tabs defaultActiveKey="active" items={[
          {
            key: 'active',
            label: '活跃订阅',
            children: <ActiveSubscriptions accountId={accountId} account={account} />,
          },
          {
            key: 'canceled',
            label: '已取消订阅（全部账号）',
            children: <CanceledSubscriptions />,
          },
        ]} />
      </Card>
    </div>
  );
};

export default Subscriptions;
