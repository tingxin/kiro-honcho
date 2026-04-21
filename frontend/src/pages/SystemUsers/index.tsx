import React from 'react';
import { Button, Space, Tag, Modal, Form, Input, message, Popconfirm, Card, Typography } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import api from '../../lib/api';
import ResponsiveList from '../../components/ResponsiveList';

const { Title } = Typography;

interface SystemUser {
    id: number;
    username: string;
    email: string | null;
    is_active: boolean;
    is_admin: boolean;
}

const SystemUsers: React.FC = () => {
    const [users, setUsers] = React.useState<SystemUser[]>([]);
    const [loading, setLoading] = React.useState(false);
    const [createVisible, setCreateVisible] = React.useState(false);
    const [form] = Form.useForm();
    const { t } = useTranslation();

    const fetchUsers = React.useCallback(async () => {
        setLoading(true);
        try {
            const resp = await api.get<SystemUser[]>('/auth/users');
            setUsers(resp.data);
        } catch (error: any) {
            message.error(error.response?.status === 403 ? 'Admin only' : t('common.failed'));
        } finally {
            setLoading(false);
        }
    }, [t]);

    React.useEffect(() => { fetchUsers(); }, [fetchUsers]);

    const handleCreate = async (values: { username: string; password: string; email?: string }) => {
        try {
            await api.post('/auth/users', values);
            message.success(t('systemUsers.createSuccess'));
            setCreateVisible(false);
            form.resetFields();
            fetchUsers();
        } catch (error: any) {
            message.error(error.response?.data?.detail || t('systemUsers.createFailed'));
        }
    };

    const handleDelete = async (userId: number) => {
        try {
            await api.delete(`/auth/users/${userId}`);
            message.success(t('systemUsers.deleteSuccess'));
            fetchUsers();
        } catch (error: any) {
            message.error(error.response?.data?.detail || t('systemUsers.deleteFailed'));
        }
    };

    const handleResetPassword = async (userId: number) => {
        const newPwd = prompt(t('systemUsers.resetPasswordPrompt'));
        if (!newPwd) return;
        try {
            await api.post(`/auth/users/${userId}/reset-password`, { new_password: newPwd });
            message.success(t('systemUsers.resetSuccess'));
        } catch (error: any) {
            message.error(error.response?.data?.detail || t('systemUsers.resetFailed'));
        }
    };

    const columns = [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
        { title: t('common.username'), dataIndex: 'username', key: 'username' },
        { title: t('common.email'), dataIndex: 'email', key: 'email', render: (v: string | null) => v || '-' },
        {
            title: t('systemUsers.role'), key: 'role', width: 80,
            render: (_: unknown, r: SystemUser) => r.is_admin
                ? <Tag color="red">{t('systemUsers.admin')}</Tag>
                : <Tag>{t('systemUsers.user')}</Tag>,
        },
        {
            title: t('common.actions'), key: 'actions', width: 180,
            render: (_: unknown, record: SystemUser) => (
                <Space>
                    <Button type="link" size="small" onClick={() => handleResetPassword(record.id)}>
                        {t('systemUsers.resetPassword')}
                    </Button>
                    {!record.is_admin && (
                        <Popconfirm title={t('systemUsers.deleteConfirm')} onConfirm={() => handleDelete(record.id)}>
                            <Button type="link" size="small" danger>{t('common.delete')}</Button>
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                <Title level={3} style={{ margin: 0 }}>{t('systemUsers.title')}</Title>
                <Space>
                    <Button icon={<ReloadOutlined />} onClick={fetchUsers}>{t('common.refresh')}</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
                        {t('systemUsers.addUser')}
                    </Button>
                </Space>
            </div>
            <Card>
                <ResponsiveList columns={columns} dataSource={users} rowKey="id" loading={loading} pagination={false} />
            </Card>
            <Modal title={t('systemUsers.addUser')} open={createVisible} onOk={() => form.submit()}
                onCancel={() => { setCreateVisible(false); form.resetFields(); }}
                okText={t('common.confirm')} cancelText={t('common.cancel')}>
                <Form form={form} onFinish={handleCreate} layout="vertical">
                    <Form.Item name="username" label={t('common.username')} rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="password" label={t('systemUsers.password')} rules={[{ required: true, min: 6 }]}>
                        <Input.Password />
                    </Form.Item>
                    <Form.Item name="email" label={t('common.email')}>
                        <Input />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default SystemUsers;
