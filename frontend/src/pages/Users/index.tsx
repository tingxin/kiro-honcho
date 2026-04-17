import React from 'react';
import { Table, Button, Space, Input, Tag, Modal, Form, message } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import styles from './Users.module.css';
import { userService, User } from '../../services/users';
import { useAccountStore } from '../../stores/accountStore';

const { Search } = Input;

const Users: React.FC = () => {
  const [users, setUsers] = React.useState<User[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [createModalVisible, setCreateModalVisible] = React.useState(false);
  const [form] = Form.useForm();
  
  const { currentAccount } = useAccountStore();

  const fetchUsers = React.useCallback(async () => {
    if (!currentAccount) return;
    setLoading(true);
    try {
      const data = await userService.listUsers(currentAccount.id);
      setUsers(data);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [currentAccount]);

  React.useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (values: Record<string, unknown>) => {
    if (!currentAccount) return;
    try {
      await userService.createUser(currentAccount.id, values as any);
      message.success('用户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (error) {
      message.error('用户创建失败');
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'userName', key: 'userName' },
    { title: '显示名称', dataIndex: 'displayName', key: 'displayName' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'ENABLED' ? 'green' : 'red'}>
          {status === 'ENABLED' ? '已启用' : '已禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: User) => (
        <Space>
          <Button type="link" onClick={() => message.info('密码重置功能开发中')}>
            重置密码
          </Button>
          <Button type="link" danger onClick={() => message.info('删除功能开发中: ' + record.userId)}>
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className={styles.users}>
      <div className={styles.header}>
        <Search placeholder="搜索用户" style={{ width: 300 }} onSearch={() => {}} />
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            创建用户
          </Button>
        </Space>
      </div>
      
      <Table
        className={styles.table}
        columns={columns}
        dataSource={users}
        rowKey="userId"
        loading={loading}
      />

      <Modal
        title="创建用户"
        open={createModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setCreateModalVisible(false)}
      >
        <Form form={form} onFinish={handleCreateUser} layout="vertical">
          <Form.Item name="userName" label="用户名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="displayName" label="显示名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users;
