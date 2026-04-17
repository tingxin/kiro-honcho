import React from 'react';
import { Layout as AntLayout, Menu, Dropdown, Avatar, Space, Spin } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined, DownOutlined, CloudServerOutlined } from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useAccountStore } from '../../stores/accountStore';
import AccountSelector from './AccountSelector';
import styles from './Layout.module.css';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  {
    key: '/dashboard',
    icon: <SettingOutlined />,
    label: '仪表盘',
  },
  {
    key: '/accounts',
    icon: <CloudServerOutlined />,
    label: 'AWS 账号',
  },
  {
    key: '/users',
    icon: <UserOutlined />,
    label: '用户管理',
  },
  {
    key: '/subscriptions',
    icon: <SettingOutlined />,
    label: '订阅管理',
  },
];

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { accounts, currentAccount, isLoading, fetchAccounts, setCurrentAccount } = useAccountStore();

  React.useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        navigate('/login');
      },
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
          selectedKeys={[location.pathname]}
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
    </AntLayout>
  );
};

export default Layout;
