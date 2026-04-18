import { useState, useEffect } from 'react'
import {
  Card, Button, Modal, Form, Input, Select, Space, Tag, message,
  Popconfirm, Typography, Descriptions,
} from 'antd'
import {
  PlusOutlined, SyncOutlined, CheckCircleOutlined, DeleteOutlined,
  CloudServerOutlined, EyeOutlined,
} from '@ant-design/icons'
import { accountService, AWSAccount, CreateAccountRequest } from '../../services/accounts'
import { useAccountStore } from '../../stores/accountStore'
import ResponsiveList from '../../components/ResponsiveList'
import styles from './Accounts.module.css'

const { Title } = Typography
const { Option } = Select
const { TextArea } = Input

const regions = [
  'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
  'eu-west-1', 'eu-west-2', 'eu-central-1',
  'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2',
]

export default function Accounts() {
  const [accounts, setAccounts] = useState<AWSAccount[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailAccount, setDetailAccount] = useState<AWSAccount | null>(null)
  const [form] = Form.useForm()
  const [verifying, setVerifying] = useState<number | null>(null)
  const [syncing, setSyncing] = useState<number | null>(null)
  const { fetchAccounts: refreshStore } = useAccountStore()

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    setLoading(true)
    try {
      const response = await accountService.list()
      setAccounts(response.accounts)
      refreshStore() // 刷新全局 store，让侧边栏菜单更新
    } catch (error) {
      message.error('Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: CreateAccountRequest) => {
    try {
      const account = await accountService.create(values)
      message.success(`Account "${account.name}" created, verifying...`)
      setModalVisible(false)
      form.resetFields()
      await loadAccounts()

      // 自动 verify + sync
      try {
        const verifyResult = await accountService.verify(account.id)
        if (verifyResult.status === 'active') {
          message.success('Account verified, syncing data...')
          const syncResult = await accountService.sync(account.id)
          message.success(`Synced ${syncResult.synced_users} users, ${syncResult.synced_subscriptions} subscriptions`)
        } else {
          message.warning(`Verification issues: ${verifyResult.message}`)
        }
        loadAccounts()
      } catch (e) {
        message.warning('Auto verify/sync failed, please do it manually')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to create account')
    }
  }

  const handleVerify = async (accountId: number) => {
    setVerifying(accountId)
    try {
      const result = await accountService.verify(accountId)
      if (result.status === 'active') {
        message.success('Account verified successfully')
      } else {
        message.warning(`Verification issues: ${result.message}`)
      }
      loadAccounts()
    } catch (error) {
      message.error('Verification failed')
    } finally {
      setVerifying(null)
    }
  }

  const handleSync = async (accountId: number) => {
    setSyncing(accountId)
    try {
      const result = await accountService.sync(accountId)
      message.success(`Synced ${result.synced_users} users, ${result.synced_subscriptions} subscriptions`)
      loadAccounts()
    } catch (error) {
      message.error('Sync failed')
    } finally {
      setSyncing(null)
    }
  }

  const handleDelete = async (accountId: number) => {
    try {
      await accountService.delete(accountId)
      message.success('Account deleted')
      loadAccounts()
    } catch (error) {
      message.error('Failed to delete account')
    }
  }

  const getStatusTag = (status: string) => {
    const config = {
      active: { color: 'success', icon: <CheckCircleOutlined /> },
      pending: { color: 'warning', icon: <SyncOutlined spin /> },
      invalid: { color: 'error', icon: null },
    }
    const c = config[status as keyof typeof config] || { color: 'default', icon: null }
    return <Tag color={c.color} icon={c.icon}>{status}</Tag>
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 160,
      render: (name: string) => (
        <Space><CloudServerOutlined /><span>{name}</span></Space>
      ),
    },
    {
      title: 'SSO',
      dataIndex: 'sso_region',
      key: 'sso_region',
      width: 110,
    },
    {
      title: 'Kiro',
      dataIndex: 'kiro_region',
      key: 'kiro_region',
      width: 110,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: getStatusTag,
    },
    {
      title: 'IC',
      dataIndex: 'identity_store_id',
      key: 'identity_store_id',
      width: 90,
      render: (id: string) => id ? <Tag color="blue">✓</Tag> : <Tag>-</Tag>,
    },
    {
      title: '同步',
      dataIndex: 'sync_interval_minutes',
      key: 'sync_interval_minutes',
      width: 80,
      render: (val: number | undefined) => {
        if (!val || val <= 0) return <Tag>Off</Tag>
        return <Tag color="cyan">{val}min</Tag>
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_: any, record: AWSAccount) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />}
            onClick={() => setDetailAccount(record)}>详情</Button>
          <Button type="link" size="small"
            onClick={() => handleVerify(record.id)}
            loading={verifying === record.id}>Verify</Button>
          {record.status === 'active' && (
            <Button type="link" size="small"
              onClick={() => handleSync(record.id)}
              loading={syncing === record.id}>Sync</Button>
          )}
          <Popconfirm title="Delete this account?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className={styles.accounts}>
      <div className={styles.header}>
        <Title level={2}>AWS Accounts</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          Add Account
        </Button>
      </div>

      <Card>
        <ResponsiveList columns={columns} dataSource={accounts} rowKey="id" loading={loading}
          pagination={{ pageSize: 10 }} scroll={{ x: 900 }} />
      </Card>

      {/* 详情弹窗 */}
      <Modal title="账号详情" open={!!detailAccount} onCancel={() => setDetailAccount(null)}
        footer={<Button onClick={() => setDetailAccount(null)}>关闭</Button>} width={640}>
        {detailAccount && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="名称">{detailAccount.name}</Descriptions.Item>
            <Descriptions.Item label="描述">{detailAccount.description || '-'}</Descriptions.Item>
            <Descriptions.Item label="Access Key ID">{detailAccount.access_key_masked || '******'}</Descriptions.Item>
            <Descriptions.Item label="SSO Region">{detailAccount.sso_region}</Descriptions.Item>
            <Descriptions.Item label="Kiro Region">{detailAccount.kiro_region}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(detailAccount.status)}</Descriptions.Item>
            <Descriptions.Item label="Instance ARN">{detailAccount.instance_arn || '-'}</Descriptions.Item>
            <Descriptions.Item label="Identity Store ID">{detailAccount.identity_store_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="自动同步">
              {detailAccount.sync_interval_minutes ? `每 ${detailAccount.sync_interval_minutes} 分钟` : '关闭'}
            </Descriptions.Item>
            <Descriptions.Item label="上次同步">
              {detailAccount.last_synced ? new Date(detailAccount.last_synced).toLocaleString() : '从未'}
            </Descriptions.Item>
            <Descriptions.Item label="上次验证">
              {detailAccount.last_verified ? new Date(detailAccount.last_verified).toLocaleString() : '从未'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(detailAccount.created_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 添加账号弹窗 */}
      <Modal title="Add AWS Account" open={modalVisible}
        onCancel={() => { setModalVisible(false); form.resetFields() }}
        footer={null} width={600}>
        <Form form={form} layout="vertical" onFinish={handleCreate}
          initialValues={{ sso_region: 'us-east-2', kiro_region: 'us-east-1', sync_interval_minutes: 0 }}>
          <Form.Item name="name" label="Account Name"
            rules={[{ required: true, message: 'Please enter account name' }]}>
            <Input placeholder="My AWS Account" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description" />
          </Form.Item>
          <Form.Item name="access_key_id" label="Access Key ID"
            rules={[{ required: true, message: 'Please enter Access Key ID' }]}>
            <Input placeholder="AKIA..." />
          </Form.Item>
          <Form.Item name="secret_access_key" label="Secret Access Key"
            rules={[{ required: true, message: 'Please enter Secret Access Key' }]}>
            <Input.Password placeholder="Secret Access Key" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="sso_region" label="SSO Region" style={{ marginBottom: 0, width: 200 }}>
              <Select>{regions.map(r => <Option key={r} value={r}>{r}</Option>)}</Select>
            </Form.Item>
            <Form.Item name="kiro_region" label="Kiro Region" style={{ marginBottom: 0, width: 200 }}>
              <Select>{regions.map(r => <Option key={r} value={r}>{r}</Option>)}</Select>
            </Form.Item>
          </Space>
          <Form.Item name="sync_interval_minutes" label="Auto Sync Interval" style={{ marginTop: 16 }}
            extra="0 = disabled. Recommended: 30 or 60 minutes.">
            <Select>
              <Option value={0}>Disabled</Option>
              <Option value={5}>Every 5 min</Option>
              <Option value={15}>Every 15 min</Option>
              <Option value={30}>Every 30 min</Option>
              <Option value={60}>Every 60 min</Option>
            </Select>
          </Form.Item>
          <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => { setModalVisible(false); form.resetFields() }}>Cancel</Button>
              <Button type="primary" htmlType="submit">Add Account</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
