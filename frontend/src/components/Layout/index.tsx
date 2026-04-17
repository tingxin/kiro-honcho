import React, { useState, useMemo } from 'react';
import { Layout as AntLayout, Menu, Dropdown, Avatar, Space, Spin } from 'antd';
import {
  UserOutlined, LogoutOutlined, DownOutlined,
  CloudServerOutlined, KeyOutlined, SafetyCertificateOutlined,
  FileTextOutlined, DashboardOutlined,
} from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useAccountStore } from '../../stores/accountStore';
import AccountSelector from './AccountSelector';
import ChangePasswordModal from '../ChangePasswordModal';
import styles from './Layout.module.css';

const { Header, Sider, Content } = AntLayout;

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { accounts, currentAccount, isLoading, fetchAccounts, setCurrentAccount } = useAccountStore();
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);

  React.useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const accountId = currentAccount?.id;

  const menuItems = useMemo(() => [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/accounts',
      icon: <CloudServerOutlined />,
      label: 'AWS 账号',
    },
    ...(accountId
      ? [
        {
          key: `/accounts/${accountId}/users`,
          icon: <UserOutlined />,
          label: '用户管理',
        },
        {
          key: `/accounts/${accountId}/subscriptions`,
          icon: <SafetyCertificateOutlined />,
          label: '订阅管理',
        },
        {
          key: `/accounts/${accountId}/logs`,
          icon: <FileTextOutlined />,
          label: '操作日志',
        },
      ]
      : []),
  ], [accountId]);

  const selectedKeys = useMemo(() => {
    const path = location.pathname;
    const match = menuItems.find((item) => path === item.key || (item.key !== '/' && path.startsWith(item.key)));
    return match ? [match.key] : [];
  }, [location.pathname, menuItems]);

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'changePassword',
      icon: <KeyOutlined />,
      label: '修改密码',
      onClick: () => setPasswordModalOpen(true),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <AntLayout className={styles.layout}>
      <Sider width={200} className={styles.sider}>
        <div className={styles.logo}>
          <h2>Kiro Honcho</h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          className={styles.menu}
        />
      </Sider>
      <AntLayout>
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            {isLoading ? (
              <Spin size="small" />
            ) : (
              <AccountSelector
                accounts={accounts}
                currentAccount={currentAccount}
                onSelect={setCurrentAccount}
              />
            )}
          </div>
          <div className={styles.headerRight}>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space className={styles.userMenu}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.username || 'Admin'}</span>
                <DownOutlined />
              </Space>
            </Dropdown>
          </div>
        </Header>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </AntLayout>
      <ChangePasswordModal
        open={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
      />
    </AntLayout>
  );
};

export default Layout;
