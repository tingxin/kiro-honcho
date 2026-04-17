import React from 'react';
import { Table, Button, Space, Tag, Modal, Form, Select, message } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import styles from './Subscriptions.module.css';
import { subscriptionService, Subscription } from '../../services/subscriptions';
import { useAccountStore } from '../../stores/accountStore';

const Subscriptions: React.FC = () => {
  const [subscriptions, setSubscriptions] = React.useState<Subscription[]>([]);
  const [loading, setLoading] = React.useState(false);
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
    } catch (error) {
      message.error('获取订阅列表失败');
    } finally {
      setLoading(false);
    }
  }, [currentAccount]);

  React.useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const handleChangePlan = async (values: { planType: string }) => {
    if (!currentAccount || !selectedSubscription) return;
    try {
      await subscriptionService.update(currentAccount.id, selectedSubscription.id, values.planType);
      message.success('套餐变更成功');
      setChangePlanModalVisible(false);
      form.resetFields();
      fetchSubscriptions();
    } catch (error) {
      message.error('套餐变更失败');
    }
  };

  const columns = [
    { title: '用户', dataIndex: 'userName', key: 'userName' },
    { title: '当前套餐', dataIndex: 'subscriptionType', key: 'subscriptionType' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ACTIVE' ? 'green' : 'red'}>
          {status === 'ACTIVE' ? '已激活' : '已停用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: Subscription) => (
        <Space>
          <Button 
            type="link" 
            onClick={() => {
              setSelectedSubscription(record);
              setChangePlanModalVisible(true);
            }}
          >
            变更套餐
          </Button>
          <Button type="link" danger onClick={() => message.info('取消订阅功能开发中')}>
            取消订阅
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className={styles.subscriptions}>
      <div className={styles.header}>
        <h2>订阅管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchSubscriptions}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => message.info('添加订阅功能开发中')}>
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
      />

      <Modal
        title="变更套餐"
        open={changePlanModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setChangePlanModalVisible(false)}
      >
        <Form form={form} onFinish={handleChangePlan} layout="vertical">
          <Form.Item name="planType" label="套餐类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Q Developer Pro</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Q Developer Pro+</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Subscriptions;
