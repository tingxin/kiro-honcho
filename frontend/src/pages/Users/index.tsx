import React from 'react';
import { Table, Button, Space, Input, Tag, Modal, Form, message, Popconfirm, Switch, Select } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import styles from './Users.module.css';
import { userService, User } from '../../services/users';
import { useAccountStore } from '../../stores/accountStore';

const { Search } = Input;

const Users: React.FC = () => {
  const [users, setUsers] = React.useState<User[]>([]);
  const [total, setTotal] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [createModalVisible, setCreateModalVisible] = React.useState(false);
  const [searchText, setSearchText] = React.useState('');
  const [form] = Form.useForm();

  const { currentAccount } = useAccountStore();

  const fetchUsers = React.useCallback(async () => {
    if (!currentAccount) return;
    setLoading(true);
    try {
      const data = await userService.listUsers(currentAccount.id, 0, 100, searchText || undefined);
      setUsers(data.users);
      setTotal(data.total);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [currentAccount, searchText]);

  React.useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (values: Record<string, unknown>) => {
    if (!currentAccount) return;
    try {
      await userService.createUser(currentAccount.id, {
        email: values.email as string,
        given_name: values.given_name as string,
        family_name: values.family_name as string,
        display_name: values.display_name as string | undefined,
        user_name: values.user_name as string | undefined,
        auto_subscribe: values.auto_subscribe as boolean ?? true,
        subscription_type: values.subscription_type as string | undefined,
        send_password_reset: values.send_password_reset as boolean ?? true,
      });
      message.success('用户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '用户创建失败');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!currentAccount) return;
    try {
      await userService.deleteUser(currentAccount.id, userId);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '用户删除失败');
    }
  };

  const handleResetPassword = async (userId: number) => {
    if (!currentAccount) return;
    try {
      const result = await userService.resetPassword(currentAccount.id, userId);
      if (result.success) {
        message.success('密码重置邮件已发送');
      } else {
        message.warning(result.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码重置失败');
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'user_name', key: 'user_name' },
    { title: '显示名称', dataIndex: 'display_name', key: 'display_name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '订阅',
      key: 'subscription',
      render: (_: unknown, record: User) =>
        record.has_subscription ? (
          <Tag color="blue">{record.subscription_type}</Tag>
        ) : (
          <Tag>无</Tag>
        ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'enabled' ? 'green' : 'red'}>
          {status === 'enabled' ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: User) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleResetPassword(record.id)}>
            重置密码
          </Button>
          <Popconfirm
            title="确定删除该用户？此操作不可恢复。"
            onConfirm={() => handleDeleteUser(record.id)}
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className={styles.users}>
      <div className={styles.header}>
        <Search
          placeholder="搜索用户（邮箱/姓名）"
          style={{ width: 300 }}
          onSearch={(value) => setSearchText(value)}
          allowClear
        />
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            创建用户
          </Button>
        </Space>
      </div>

      <Table
        className={styles.table}
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: 100, showTotal: (t) => `共 ${t} 个用户` }}
      />

      <Modal
        title="创建用户"
        open={createModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        width={520}
      >
        <Form
          form={form}
          onFinish={handleCreateUser}
          layout="vertical"
          initialValues={{
            auto_subscribe: true,
            subscription_type: 'Q_DEVELOPER_STANDALONE_PRO',
            send_password_reset: true,
          }}
        >
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}>
            <Input placeholder="user@example.com" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="given_name" label="名" rules={[{ required: true, message: '请输入名' }]} style={{ flex: 1 }}>
              <Input placeholder="名" />
            </Form.Item>
            <Form.Item name="family_name" label="姓" rules={[{ required: true, message: '请输入姓' }]} style={{ flex: 1 }}>
              <Input placeholder="姓" />
            </Form.Item>
          </Space>
          <Form.Item name="display_name" label="显示名称">
            <Input placeholder="可选，默认为 名+姓" />
          </Form.Item>
          <Form.Item name="user_name" label="用户名">
            <Input placeholder="可选，默认使用邮箱" />
          </Form.Item>
          <Form.Item name="auto_subscribe" label="自动分配订阅" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.auto_subscribe !== cur.auto_subscribe}>
            {({ getFieldValue }) =>
              getFieldValue('auto_subscribe') ? (
                <Form.Item name="subscription_type" label="订阅类型">
                  <Select>
                    <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Q Developer Pro</Select.Option>
                    <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Q Developer Pro+</Select.Option>
                  </Select>
                </Form.Item>
              ) : null
            }
          </Form.Item>
          <Form.Item name="send_password_reset" label="发送密码重置邮件" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users;
