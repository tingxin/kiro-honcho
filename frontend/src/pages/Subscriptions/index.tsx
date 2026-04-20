import React from 'react';
import {
  Button, Space, Tag, Modal, Form, Select, Input, message,
  Popconfirm, Card, Typography, Switch, Upload, Divider, Alert, Tabs,
} from 'antd';
import { PlusOutlined, ReloadOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { useParams, useNavigate } from 'react-router-dom';
import styles from './Subscriptions.module.css';
import { subscriptionService, Subscription } from '../../services/subscriptions';
import { userService, User } from '../../services/users';
import { accountService, AWSAccount } from '../../services/accounts';
import ResponsiveList from '../../components/ResponsiveList';

const { Text } = Typography;
const { Search } = Input;

const planLabels: Record<string, string> = {
  Q_DEVELOPER_STANDALONE_PRO: 'Kiro Pro',
  Q_DEVELOPER_STANDALONE_PRO_PLUS: 'Kiro Pro+',
  Q_DEVELOPER_STANDALONE_POWER: 'Kiro Power',
  KIRO_ENTERPRISE_PRO: 'Kiro Pro',
  KIRO_ENTERPRISE_PRO_PLUS: 'Kiro Pro+',
  KIRO_ENTERPRISE_PRO_POWER: 'Kiro Power',
};

// 计算用户生命周期状态
function getUserLifecycleStatus(user: User): 'unsubscribed' | 'email_unverified' | 'pending' | 'active' {
  const hasSub = user.has_subscription;
  const subStatus = (user.subscription_status || '').toUpperCase();

  if (!hasSub && !user.pending_subscription_type) {
    return 'unsubscribed';
  }
  if (hasSub || user.pending_subscription_type) {
    if (!user.email_verified) return 'email_unverified';
    if (subStatus === 'ACTIVE') return 'active';
    return 'pending';
  }
  return 'unsubscribed';
}

function getStatusTag(status: string) {
  switch (status) {
    case 'unsubscribed': return <Tag>未订阅</Tag>;
    case 'email_unverified': return <Tag color="red">邮箱未激活</Tag>;
    case 'pending': return <Tag color="orange">Pending</Tag>;
    case 'active': return <Tag color="green">Active</Tag>;
    default: return <Tag>{status}</Tag>;
  }
}

// ========== Main Page ==========
const SubscriptionManagement: React.FC = () => {
  const { accountId: accountIdStr } = useParams<{ accountId: string }>();
  const navigate = useNavigate();
  const accountId = Number(accountIdStr);

  const [account, setAccount] = React.useState<AWSAccount | null>(null);
  const [users, setUsers] = React.useState<User[]>([]);
  const [total, setTotal] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [searchText, setSearchText] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string | undefined>(undefined);

  // Modals
  const [createModalVisible, setCreateModalVisible] = React.useState(false);
  const [csvModalVisible, setCsvModalVisible] = React.useState(false);
  const [changePlanModal, setChangePlanModal] = React.useState<User | null>(null);
  const [csvFile, setCsvFile] = React.useState<UploadFile | null>(null);
  const [batchLogs, setBatchLogs] = React.useState<string[]>([]);
  const [batchRunning, setBatchRunning] = React.useState(false);
  const batchLogRef = React.useRef<HTMLDivElement>(null);

  const [createForm] = Form.useForm();
  const [changePlanForm] = Form.useForm();

  React.useEffect(() => {
    if (!accountId || isNaN(accountId)) { navigate('/accounts'); return; }
    accountService.get(accountId).then(setAccount).catch(() => navigate('/accounts'));
  }, [accountId, navigate]);

  const fetchUsers = React.useCallback(async () => {
    if (!accountId || isNaN(accountId)) return;
    setLoading(true);
    try {
      const data = await userService.listUsers(accountId, 0, 500, searchText || undefined, statusFilter);
      setUsers(data.users);
      setTotal(data.total);
    } catch { message.error('获取用户列表失败'); }
    finally { setLoading(false); }
  }, [accountId, searchText, statusFilter]);

  React.useEffect(() => { fetchUsers(); }, [fetchUsers]);

  // ===== Handlers =====
  const handleCreateUser = async (values: Record<string, any>) => {
    setCreateModalVisible(false);
    createForm.resetFields();
    try {
      await userService.createUser(accountId, {
        email: values.email,
        given_name: values.given_name || undefined,
        family_name: values.family_name || undefined,
        auto_subscribe: values.auto_subscribe ?? true,
        subscription_type: values.subscription_type,
        send_password_reset: true,
      });
      message.success('用户已创建，后台正在处理邮件和订阅');
      fetchUsers();
    } catch (e: any) { message.error(e.response?.data?.detail || '创建失败'); }
  };

  const handleSubscribe = async (user: User) => {
    const subType = await new Promise<string | null>((resolve) => {
      Modal.confirm({
        title: `为 ${user.email} 分配订阅`,
        content: (
          <Select defaultValue="Q_DEVELOPER_STANDALONE_PRO" style={{ width: '100%', marginTop: 8 }}
            onChange={(v) => (window as any).__subType = v}>
            <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Kiro Pro</Select.Option>
            <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Kiro Pro+</Select.Option>
            <Select.Option value="Q_DEVELOPER_STANDALONE_POWER">Kiro Power</Select.Option>
          </Select>
        ),
        onOk: () => resolve((window as any).__subType || 'Q_DEVELOPER_STANDALONE_PRO'),
        onCancel: () => resolve(null),
      });
    });
    if (!subType) return;
    try {
      await subscriptionService.create(accountId, {
        principal_id: user.user_id,
        subscription_type: subType,
      });
      message.success('订阅已分配');
      fetchUsers();
    } catch (e: any) { message.error(e.response?.data?.detail || '分配失败'); }
  };

  const handleChangePlan = async (values: { subscription_type: string }) => {
    if (!changePlanModal) return;
    // Find subscription ID from the subscriptions list
    try {
      const subs = await subscriptionService.list(accountId);
      const sub = subs.subscriptions.find(s => s.principal_id === changePlanModal.user_id);
      if (!sub) { message.error('未找到订阅'); return; }
      await subscriptionService.update(accountId, sub.id, values.subscription_type);
      message.success('套餐变更成功');
      setChangePlanModal(null);
      changePlanForm.resetFields();
      fetchUsers();
    } catch (e: any) { message.error(e.response?.data?.detail || '变更失败'); }
  };

  const handleCancelSubscription = async (user: User) => {
    try {
      const subs = await subscriptionService.list(accountId);
      const sub = subs.subscriptions.find(s => s.principal_id === user.user_id);
      if (!sub) { message.error('未找到订阅'); return; }
      await subscriptionService.delete(accountId, sub.id);
      message.success('订阅已取消');
      fetchUsers();
    } catch (e: any) { message.error(e.response?.data?.detail || '取消失败'); }
  };

  const handleResendEmail = async (userId: number) => {
    try {
      await userService.resetPassword(accountId, userId);
      message.success('激活邮件已重新发送');
    } catch { message.error('发送失败'); }
  };

  const handleResetPassword = async (userId: number) => {
    try {
      await userService.resetPassword(accountId, userId);
      message.success('密码重置邮件已发送');
    } catch { message.error('发送失败'); }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await userService.deleteUser(accountId, userId);
      message.success('用户已删除');
      fetchUsers();
    } catch (e: any) { message.error(e.response?.data?.detail || '删除失败'); }
  };

  // CSV batch
  const handleCsvUpload = async () => {
    if (!csvFile?.originFileObj) return;
    setCsvModalVisible(false);
    const file = csvFile.originFileObj;
    setCsvFile(null);
    setBatchRunning(true);
    setBatchLogs(['⏳ 正在上传...']);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('send_password_reset', 'true');
      const authData = localStorage.getItem('kiro-auth');
      let token = '';
      if (authData) { try { token = JSON.parse(authData).state?.accessToken || ''; } catch { } }
      const response = await fetch(`/api/accounts/${accountId}/batch/users/csv/stream`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData,
      });
      if (!response.ok || !response.body) {
        const errText = await response.text();
        setBatchLogs(prev => [...prev, `❌ 失败: ${errText}`]); return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.message) {
                const time = new Date().toLocaleTimeString();
                setBatchLogs(prev => [...prev, `[${time}] ${data.message}`]);
              }
            } catch { }
          }
        }
      }
    } catch (e: any) { setBatchLogs(prev => [...prev, `❌ ${e.message}`]); }
    finally { setBatchRunning(false); fetchUsers(); }
  };

  React.useEffect(() => {
    if (batchLogRef.current) batchLogRef.current.scrollTop = batchLogRef.current.scrollHeight;
  }, [batchLogs]);

  const downloadCsvTemplate = () => {
    const csv = 'email,subscription_type\nuser@example.com,Q_DEVELOPER_STANDALONE_PRO\n';
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'users_template.csv'; a.click();
  };

  // ===== Columns =====
  const columns = [
    { title: '邮箱', dataIndex: 'email', key: 'email', ellipsis: true, width: 180 },
    { title: '用户名', dataIndex: 'user_name', key: 'user_name', width: 90, ellipsis: true },
    {
      title: '套餐', key: 'plan', width: 90,
      render: (_: unknown, r: User) => {
        const type = r.subscription_type || r.pending_subscription_type;
        return type ? <Tag color="blue">{planLabels[type] || type}</Tag> : '-';
      },
    },
    {
      title: '状态', key: 'status', width: 100,
      render: (_: unknown, r: User) => getStatusTag(getUserLifecycleStatus(r)),
    },
    {
      title: '操作', key: 'actions', width: 280,
      render: (_: unknown, record: User) => {
        const status = getUserLifecycleStatus(record);
        return (
          <Space wrap>
            {status === 'unsubscribed' && (
              <Button type="link" size="small" onClick={() => handleSubscribe(record)}>订阅</Button>
            )}
            {status === 'email_unverified' && (
              <Button type="link" size="small" onClick={() => handleResendEmail(record.id)}>重发邮件</Button>
            )}
            {(status === 'pending' || status === 'active') && (
              <>
                <Button type="link" size="small" onClick={() => {
                  setChangePlanModal(record);
                  changePlanForm.setFieldsValue({ subscription_type: record.subscription_type });
                }}>变更套餐</Button>
                <Popconfirm title="确定取消订阅？" onConfirm={() => handleCancelSubscription(record)}>
                  <Button type="link" size="small" danger>取消订阅</Button>
                </Popconfirm>
              </>
            )}
            <Button type="link" size="small" onClick={() => handleResetPassword(record.id)}>重置密码</Button>
            <Popconfirm
              title="删除用户"
              description={record.has_subscription ? "删除前会自动取消该用户的 Kiro 订阅" : "确定删除该用户？"}
              onConfirm={() => handleDeleteUser(record.id)}
            >
              <Button type="link" size="small" danger>删除</Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <div className={styles.subscriptions}>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Text strong>当前账号:</Text>
          <Tag color="blue">{account?.name || '...'}</Tag>
          <Tag color={account?.status === 'active' ? 'green' : 'orange'}>{account?.status}</Tag>
        </Space>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        <Space wrap>
          <Search placeholder="搜索邮箱/用户名" style={{ width: 220 }} onSearch={setSearchText} allowClear />
          <Select placeholder="状态" allowClear style={{ width: 130 }} value={statusFilter} onChange={setStatusFilter}>
            <Select.Option value="UNVERIFIED">邮箱未激活</Select.Option>
            <Select.Option value="PENDING">Pending</Select.Option>
            <Select.Option value="ACTIVE">Active</Select.Option>
            <Select.Option value="NONE">未订阅</Select.Option>
          </Select>
        </Space>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={fetchUsers}>刷新</Button>
          <Button icon={<UploadOutlined />} onClick={() => setCsvModalVisible(true)}>CSV 导入</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>添加用户</Button>
        </Space>
      </div>

      <ResponsiveList columns={columns} dataSource={users} rowKey="id" loading={loading}
        pagination={{ total, pageSize: 500, showTotal: (t: number) => `共 ${t} 人` }}
        scroll={{ x: 740 }} />

      {/* 创建用户 */}
      <Modal title="添加用户" open={createModalVisible} onOk={() => createForm.submit()}
        onCancel={() => { setCreateModalVisible(false); createForm.resetFields(); }} width={480}>
        <Alert message="用户将加入 Identity Center 并分配 Kiro 订阅，同时发送激活邮件" type="info" showIcon style={{ marginBottom: 16 }} />
        <Form form={createForm} onFinish={handleCreateUser} layout="vertical"
          initialValues={{ auto_subscribe: true, subscription_type: 'Q_DEVELOPER_STANDALONE_PRO' }}>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="user@example.com" />
          </Form.Item>
          <Space style={{ width: '100%' }}>
            <Form.Item name="given_name" label="名" style={{ flex: 1 }}><Input placeholder="可选" /></Form.Item>
            <Form.Item name="family_name" label="姓" style={{ flex: 1 }}><Input placeholder="可选" /></Form.Item>
          </Space>
          <Form.Item name="auto_subscribe" label="立即分配订阅" valuePropName="checked"><Switch /></Form.Item>
          <Form.Item noStyle shouldUpdate={(p, c) => p.auto_subscribe !== c.auto_subscribe}>
            {({ getFieldValue }) => getFieldValue('auto_subscribe') ? (
              <Form.Item name="subscription_type" label="套餐">
                <Select>
                  <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Kiro Pro</Select.Option>
                  <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Kiro Pro+</Select.Option>
                  <Select.Option value="Q_DEVELOPER_STANDALONE_POWER">Kiro Power</Select.Option>
                </Select>
              </Form.Item>
            ) : null}
          </Form.Item>
        </Form>
      </Modal>

      {/* 变更套餐 */}
      <Modal title="变更套餐" open={!!changePlanModal} onOk={() => changePlanForm.submit()}
        onCancel={() => { setChangePlanModal(null); changePlanForm.resetFields(); }}>
        <p>用户: {changePlanModal?.email}</p>
        <Form form={changePlanForm} onFinish={handleChangePlan} layout="vertical">
          <Form.Item name="subscription_type" label="套餐" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO">Kiro Pro</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_PRO_PLUS">Kiro Pro+</Select.Option>
              <Select.Option value="Q_DEVELOPER_STANDALONE_POWER">Kiro Power</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* CSV 导入 */}
      <Modal title="CSV 批量导入" open={csvModalVisible} onOk={handleCsvUpload}
        onCancel={() => { setCsvModalVisible(false); setCsvFile(null); }}
        okText="开始导入" okButtonProps={{ disabled: !csvFile || batchRunning }}>
        <Alert message={<>必填: <Text code>email</Text>，可选: <Text code>subscription_type</Text> (默认 Pro)</>}
          type="info" showIcon style={{ marginBottom: 16 }} />
        <Button icon={<DownloadOutlined />} onClick={downloadCsvTemplate} type="dashed" block>下载模板</Button>
        <Divider />
        <Upload accept=".csv" maxCount={1} beforeUpload={() => false}
          fileList={csvFile ? [csvFile] : []} onChange={({ fileList }) => setCsvFile(fileList[0] || null)}>
          <Button icon={<UploadOutlined />} block>选择 CSV</Button>
        </Upload>
      </Modal>

      {/* 批量进度 */}
      <Modal title="批量导入进度" open={batchRunning || batchLogs.length > 0}
        closable={!batchRunning} maskClosable={false}
        footer={batchRunning ? null : <Button type="primary" onClick={() => setBatchLogs([])}>关闭</Button>} width={640}>
        <div ref={batchLogRef} style={{
          background: '#1a1a1a', color: '#e0e0e0', padding: 12, borderRadius: 6,
          fontFamily: 'monospace', fontSize: 13, lineHeight: 1.6, maxHeight: 400, overflowY: 'auto', whiteSpace: 'pre-wrap',
        }}>
          {batchLogs.map((log, i) => <div key={i}>{log}</div>)}
          {batchRunning && <div style={{ color: '#888' }}>⏳ 处理中...</div>}
        </div>
      </Modal>
    </div>
  );
};

export default SubscriptionManagement;
