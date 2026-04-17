import React, { useState, useEffect } from 'react';
import { Modal, Table, Button, Form, Input, Space, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import api from '../../lib/api';

interface AppUser {
    id: number;
    username: string;
    email: string | null;
    is_active: boolean;
    is_admin: boolean;
}

interface Props {
    open: boolean;
    onClose: () => void;
}

const UserManagementModal: React.FC<Props> = ({ open, onClose }) => {
    const [users, setUsers] = useState<AppUser[]>([]);
    const [loading, setLoading] = useState(false);
    const [createVisible, setCreateVisible] = useState(false);
    const [form] = Form.useForm();

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const resp = await api.get<AppUser[]>('/auth/users');
            setUsers(resp.data);
        } catch {
            message.error('获取用户列表失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (open) fetchUsers();
    }, [open]);

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

    const handleDelete = async (id: number) => {
        try {
            await api.delete(`/auth/users/${id}`);
            message.success('用户已删除');
            fetchUsers();
        } catch (error: any) {
            message.error(error.response?.data?.detail || '删除失败');
        }
    };

    const columns = [
        { title: '用户名', dataIndex: 'username', key: 'username' },
        { title: '邮箱', dataIndex: 'email', key: 'email', render: (v: string | null) => v || '-' },
        {
            title: '角色', key: 'role',
            render: (_: unknown, r: AppUser) => r.is_admin ? <Tag color="red">Admin</Tag> : <Tag>普通用户</Tag>,
        },
        {
            title: '操作', key: 'actions',
            render: (_: unknown, r: AppUser) =>
                r.is_admin ? null : (
                    <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
                        <Button type="link" size="small" danger>删除</Button>
                    </Popconfirm>
                ),
        },
    ];

    return (
        <Modal title="系统用户管理" open={open} onCancel={onClose} footer={null} width={600}>
            <div style={{ marginBottom: 16, textAlign: 'right' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateVisible(true)}>
                    创建用户
                </Button>
            </div>
            <Table columns={columns} dataSource={users} rowKey="id" loading={loading} size="small" pagination={false} />

            <Modal title="创建系统用户" open={createVisible} onOk={() => form.submit()}
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
        </Modal>
    );
};

export default UserManagementModal;
