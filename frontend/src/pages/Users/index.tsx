import React from 'react';
import {
  Table, Button, Space, Input, Tag, Modal, Form, message,
  Popconfirm, Switch, Select, Upload, Typography, Alert, Divider, Card,
} from 'antd';
import { PlusOutlined, ReloadOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './Users.module.css';
import { userService, User } from '../../services/users';
import { accountService, AWSAccount } from '../../services/accounts';

const { Search } = Input;
const { Text } = Typography;

const planLabels: Record<string, string> = {
  Q_DEVELOPER_STANDALONE_PRO: 'Kiro Pro',
  Q_DEVELOPER_STANDALONE_PRO_PLUS: 'Kiro Pro+',
  KIRO_ENTERPRISE_PRO: 'Kiro Pro',
  KIRO_ENTERPRISE_PRO_PLUS: 'Kiro Pro+',
};

const Users: React.FC = () => {
  const { accountId: accountIdStr } = useParams<{ accountId: string }>();
  const navigate = useNavigate();
  const accountId = Number(accountIdStr);

  const [account, setAccount] = React.useState<AWSAccount | null>(null);
  const [users, setUsers] = React.useState<User[]>([]);
  const [total, setTotal] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [createModalVisible, setCreateModalVisible] = React.useState(false);
  const [csvModalVisible, setCsvModalVisible] = React.useState(false);
  const [csvFile, setCsvFile] = React.useState<UploadFile | null>(null);
  const [csvUploading, setCsvUploading] = React.useState(false);
  const [searchText, setSearchText] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>(undefined);
  const [sortBy, setSortBy] = React.useState<string>('created_at');
  const [sortOrder, setSortOrder] = React.useState<string>('desc');
  const [form] = Form.useForm();

  // 加载账号信息
  React.useEffect(() => {
    if (!accountId || isNaN(accountId)) {
      message.error('请先选择一个 AWS 账号');
      navigate('/accounts');
      return;
    }
    accountService.get(accountId).then(setAccount).catch(() => {
      message.error('账号不存在');
      navigate('/accounts');
    });
  }, [accountId, navigate]);

  const fetchUsers = React.useCallback(async () => {
    if (!accountId || isNaN(accountId)) return;
    setLoading(true);
    try {
      const data = await userService.listUsers(
        accountId, 0, 200, searchText || undefined,
        statusFilter, sortBy, sortOrder,
      );
      setUsers(data.users);
      setTotal(data.total);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  }, [accountId, searchText, statusFilter, sortBy, sortOrder]);

  React.useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async (values: Record<string, unknown>) => {
    try {
      // 立即关闭弹窗
      setCreateModalVisible(false);
      form.resetFields();

      await userService.createUser(accountId, {
        email: values.email as string,
        given_name: values.given_name as string,
        family_name: values.family_name as string,
        display_name: values.display_name as string | undefined,
        user_name: values.user_name as string | undefined,
        auto_subscribe: values.auto_subscribe as boolean ?? true,
        subscription_type: values.subscription_type as string | undefined,
        send_password_reset: values.send_password_reset as boolean ?? true,
      });
      message.success('用户已创建，邮件发送和订阅分配正在后台执行');
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '用户创建失败');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await userService.deleteUser(accountId, userId);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '用户删除失败');
    }
  };

  const handleResetPassword = async (userId: number) => {
    try {
      const result = await userService.resetPassword(accountId, userId);
      if (result.success) {
        message.success('密码重置邮件已发送');
      } else {
        message.warning(result.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码重置失败');
    }
  };

  const handleCsvUpload = async () => {
    if (!csvFile?.originFileObj) return;
    // 立即关闭弹窗
    setCsvModalVisible(false);
    const file = csvFile.originFileObj;
    setCsvFile(null);

    setCsvUploading(true);
    try {
      const result = await userService.batchCreateUsersCSV(accountId, file);
      message.success(
        `批量导入完成: ${result.success_count} 成功, ${result.failed_count} 失败`
      );
      if (result.failed_count > 0) {
        const failedEmails = result.results
          .filter((r) => !r.success)
          .map((r) => `${r.email}: ${r.message}`)
          .join('\n');
        Modal.warning({
          title: '部分用户导入失败',
          content: <pre style={{ maxHeight: 300, overflow: 'auto' }}>{failedEmails}</pre>,
        });
      }
      fetchUsers();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'CSV 导入失败');
    } finally {
      setCsvUploading(false);
    }
  };

  const downloadCsvTemplate = () => {
    const csv = 'email,given_name,family_name,subscription_type\nuser@example.com,John,Doe,Q_DEVELOPER_STANDALONE_PRO\n';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'users_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSubscriptionTag = (record: User) => {
    if (record.has_subscription) {
      const subType = planLabels[record.subscription_type || ''] || record.subscription_type;
      return <Tag color="green">{subType}</Tag>;
    }
    if (record.pending_subscription_type) {
      return <Tag color="orange">分配中（后台重试）</Tag>;
    }
    return <Tag>无</Tag>;
  };

  const columns = [
    { title: '用户名', dataIndex: 'user_name', key: 'user_name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_: unknown, record: User) => {
        if (!record.email_verified) {
          return <Tag color="red">邮箱未激活</Tag>;
        }
        if (record.has_subscription) {
          const subStatus = (record.subscription_status || '').toUpperCase();
          if (subStatus === 'ACTIVE') return <Tag color="green">Active</Tag>;
          return <Tag color="orange">Pending</Tag>;
        }
        return <Tag color="orange">Pending</Tag>;
      },
    },
    {
      title: '订阅',
      key: 'subscription',
      width: 200,
      render: (_: unknown, record: User) => getSubscriptionTag(record),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: unknown, record: User) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleResetPassword(record.id)}>
            重置密码
          </Button>
          <Popconfirm title="确定删除该用户？" onConfirm={() => handleDeleteUser(record.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className={styles.users}>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Text strong>当前账号:</Text>
          <Tag color="blue">{account?.name || '加载中...'}</Tag>
          <Text type="secondary">SSO: {account?.sso_region}</Text>
          <Text type="secondary">Kiro: {account?.kiro_region}</Text>
          <Tag color={account?.status === 'active' ? 'green' : 'orange'}>{account?.status}</Tag>
        </Space>
      </Card>

      <div className={styles.header}>
        <Space wrap>
          <Search
            placeholder="搜索用户（邮箱/姓名）"
            style={{ width: 240 }}
            onSearch={(value) => setSearchText(value)}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 140 }}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v)}
          >
            <Select.Option value="UNVERIFIED">邮箱未激活</Select.Option>
            <Select.Option value="PENDING">Pending</Select.Option>
            <Select.Option value="ACTIVE">Active</Select.Option>
            <Select.Option value="NONE">无订阅</Select.Option>
          </Select>
          <Select
            style={{ width: 130 }}
            value={sortBy}
            onChange={(v) => setSortBy(v)}
          >
            <Select.Option value="created_at">创建时间</Select.Option>
            <Select.Option value="email">邮箱</Select.Option>
            <Select.Option value="status">状态</Select.Option>
          </Select>
          <Select
            style={{ width: 80 }}
            value={sortOrder}
            onChange={(v) => setSortOrder(v)}
          >
            <Select.Option value="desc">降序</Select.Option>
            <Select.Option value="asc">升序</Select.Option>
          </Select>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers}>刷新</Button>
          <Button icon={<UploadOutlined />} onClick={() => setCsvModalVisible(true)}>
            CSV 批量导入
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
        pagination={{ total, pageSize: 200, showTotal: (t) => `共 ${t} 个用户` }}
      />

      {/* 创建用户 Modal */}
      <Modal
        title={<span>创建用户 — <Tag color="blue">{account?.name}</Tag></span>}
        open={createModalVisible}
        onOk={() => form.submit()}
        onCancel={() => { setCreateModalVisible(false); form.resetFields(); }}
        width={520}
      >
        <Alert
          message="用户将被添加到 Identity Center 并立即分配 Kiro 订阅（状态为 PENDING，用户验证邮箱后自动变为 ACTIVE）"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
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
          <Form.Item name="auto_subscribe" label="激活后自动分配订阅" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.auto_subscribe !== cur.auto_subscribe}>
            {({ getFieldValue }) =>
              getFieldValue('auto_subscribe') ? (
                <Form.Item name="subscription_type" label="订阅类型">
                  <Select>
                    <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Kiro Pro</Select.Option>
                    <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Kiro Pro+</Select.Option>
                  </Select>
                </Form.Item>
              ) : null
            }
          </Form.Item>
          <Form.Item name="send_password_reset" label="发送邀请邮件" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* CSV 批量导入 Modal */}
      <Modal
        title={<span>CSV 批量导入 — <Tag color="blue">{account?.name}</Tag></span>}
        open={csvModalVisible}
        onOk={handleCsvUpload}
        onCancel={() => { setCsvModalVisible(false); setCsvFile(null); }}
        confirmLoading={csvUploading}
        okText="开始导入"
        okButtonProps={{ disabled: !csvFile }}
      >
        <Alert
          message="CSV 格式说明"
          description={
            <div>
              <p>必填列: <Text code>email</Text>, <Text code>given_name</Text>, <Text code>family_name</Text></p>
              <p>可选列: <Text code>subscription_type</Text> (默认 Q_DEVELOPER_STANDALONE_PRO), <Text code>display_name</Text></p>
              <p>所有用户将添加到 <Text strong>{account?.name}</Text> 账号的 Identity Center。</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button icon={<DownloadOutlined />} onClick={downloadCsvTemplate} type="dashed" block>
            下载 CSV 模板
          </Button>
          <Divider />
          <Upload
            accept=".csv"
            maxCount={1}
            beforeUpload={() => false}
            fileList={csvFile ? [csvFile] : []}
            onChange={({ fileList }) => setCsvFile(fileList[0] || null)}
          >
            <Button icon={<UploadOutlined />} block>选择 CSV 文件</Button>
          </Upload>
        </Space>
      </Modal>
    </div>
  );
};

export default Users;
