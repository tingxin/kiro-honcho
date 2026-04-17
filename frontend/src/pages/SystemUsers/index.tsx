import React from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, message, Popconfirm, Card, Typography } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import api from '../../lib/api';

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

    const fetchUsers = React.useCallback(async () => {
        setLoading(true);
        try {
            const resp = await api.get<SystemUser[]>('/auth/users');
            setUsers(resp.data);
        } catch (error: any) {
            if (error.response?.status === 403) {
                message.error('仅管理员可访问');
            } else {
                message.error('获取用户列表失败');
            }
        } finally {
            setLoading(false);
        }
    }, []);

    React.useEffect(() => { fetchUsers(); }, [fetchUsers]);

    const handleCreate = async (values: { username: string; password: string; email?: string }) => {
        try {
            await api.post('/auth/users', values);
            message.success('用户创建成功');
            setCreateVisible(false);
            form.resetFields();
            fetchUsers();
        } catch (error: any) {
            message.error(error.response?.data?.detail || '创建失败');
        }
    };

    const handleDelete = async (userId: number) => {
        try {
            await api.delete(`/auth/users/${userId}`);
            message.success('用户已删除');
            fetchUsers();
        } catch (error: any) {
            message.error(error.response?.data?.detail || '删除失败');
        }
    };

    const handleResetPassword = async (userId: number) => {
        const newPwd = prompt('请输入新密码:');
        if (!newPwd) return;
        try {
            await api.post(`/auth/users/${userId}/reset-password`, { new_password: newPwd });
            message.success('密码已重置');
        } catch (error: any) {
            message.error(error.response?.data?.detail || '重置失败');
        }
    };

    const columns = [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
        { title: '用户名', dataIndex: 'username', key: 'username' },
        { title: '邮箱', dataIndex: 'email', key: 'email', render: (v: string | null) => v || '-' },
        {
            title: '角色', key: 'role', width: 80,
            render: (_: unknown, r: SystemUser) => r.is_admin ? <Tag color="red">Admin</Tag> : <Tag>User</Tag>,
        },
        {
            title: '操作', key: 'actions', width: 180,
            render: (_: unknown, record: SystemUser) => (
                <Space>
                    <Button type="link" size="small" onClick={() => handleResetPassword(record.id)}>重置密码</Button>
                    {!record.is_admin && (
                        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
                            <Button type="link" size="small" danger>删除</Button>
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                <Title level={3} style={{ margin: 0 }}>系统用户管理</Title>
                <Space>
                    <Button icon={<ReloadOutlined />} onClick={fetchUsers}>刷新</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>添加用户</Button>
                </Space>
            </div>
            <Card>
                <Table columns={columns} dataSource={users} rowKey="id" loading={loading} pagination={false} />
            </Card>
            <Modal title="添加系统用户" open={createVisible} onOk={() => form.submit()}
                onCancel={() => { setCreateVisible(false); form.resetFields(); }}>
                <Form form={form} onFinish={handleCreate} layout="vertical">
                    <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
                        <Input.Password />
                    </Form.Item>
                    <Form.Item name="email" label="邮箱">
                        <Input />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default SystemUsers;
