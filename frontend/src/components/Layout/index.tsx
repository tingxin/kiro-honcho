import React, { useState, useMemo } from 'react';
import { Layout as AntLayout, Menu, Dropdown, Avatar, Space, Spin, Button, Drawer } from 'antd';
import {
  UserOutlined, LogoutOutlined, DownOutlined,
  CloudServerOutlined, KeyOutlined, SafetyCertificateOutlined,
  FileTextOutlined, DashboardOutlined, MenuOutlined,
} from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useAccountStore } from '../../stores/accountStore';
import AccountSelector from './AccountSelector';
import ChangePasswordModal from '../ChangePasswordModal';
import styles from './Layout.module.css';

const { Header, Sider, Content } = AntLayout;

function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(window.innerWidth < 768);
  React.useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);
  return isMobile;
}

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const { user, logout } = useAuthStore();
  const { accounts, currentAccount, isLoading, fetchAccounts, setCurrentAccount } = useAccountStore();
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  React.useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // 判断当前是否在账号管理页面（不需要显示账号选择器）
  const isAccountsPage = location.pathname === '/accounts';

  // 切换账号时，如果当前在某个账号的子页面，导航到新账号的对应页面
  const handleAccountSelect = (account: typeof currentAccount) => {
    if (!account) return;
    setCurrentAccount(account);

    // 如果当前在某个账号的子页面，跳转到新账号的对应页面
    const match = location.pathname.match(/\/accounts\/\d+\/(users|subscriptions|logs)/);
    if (match) {
      navigate(`/accounts/${account.id}/${match[1]}`);
    }
  };

  const accountId = currentAccount?.id;

  const menuItems = useMemo(() => [
    { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/accounts', icon: <CloudServerOutlined />, label: 'AWS 账号' },
    ...(accountId
      ? [
        { key: `/accounts/${accountId}/users`, icon: <UserOutlined />, label: '用户管理' },
        { key: `/accounts/${accountId}/subscriptions`, icon: <SafetyCertificateOutlined />, label: '订阅管理' },
        { key: `/accounts/${accountId}/logs`, icon: <FileTextOutlined />, label: '操作日志' },
      ]
      : []),
  ], [accountId]);

  const selectedKeys = useMemo(() => {
    const path = location.pathname;
    // 从长到短匹配，优先精确匹配
    const sorted = [...menuItems].sort((a, b) => b.key.length - a.key.length);
    const match = sorted.find((item) => path === item.key || path.startsWith(item.key + '/'));
    return match ? [match.key] : [];
  }, [location.pathname, menuItems]);

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
    if (isMobile) setDrawerOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    { key: 'changePassword', icon: <KeyOutlined />, label: '修改密码', onClick: () => setPasswordModalOpen(true) },
    ...(user?.is_admin ? [{ key: 'systemUsers', icon: <UserOutlined />, label: '系统用户管理', onClick: () => navigate('/system-users') }] : []),
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout },
  ];

  const siderMenu = (
    <>
      <div className={styles.logo}>
        <h2>Kiro Honcho</h2>
      </div>
      <Menu
        mode="inline"
        selectedKeys={selectedKeys}
        items={menuItems}
        onClick={handleMenuClick}
        className={styles.menu}
        theme="dark"
      />
    </>
  );

  return (
    <AntLayout className={styles.layout}>
      {/* Desktop: 固定侧边栏 */}
      {!isMobile && (
        <Sider width={200} className={styles.sider}>
          {siderMenu}
        </Sider>
      )}

      {/* Mobile: 抽屉侧边栏 */}
      {isMobile && (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={200}
          styles={{ body: { padding: 0, background: '#001529' } }}
          closable={false}
        >
          {siderMenu}
        </Drawer>
      )}

      <AntLayout>
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setDrawerOpen(true)}
                style={{ marginRight: 8 }}
              />
            )}
            {isLoading ? (
              <Spin size="small" />
            ) : !isAccountsPage ? (
              <AccountSelector
                accounts={accounts}
                currentAccount={currentAccount}
                onSelect={handleAccountSelect}
              />
            ) : null}
          </div>
          <div className={styles.headerRight}>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space className={styles.userMenu}>
                <Avatar size={isMobile ? 'small' : 'default'} icon={<UserOutlined />} />
                {!isMobile && <span>{user?.username || 'Admin'}</span>}
                <DownOutlined />
              </Space>
            </Dropdown>
          </div>
        </Header>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </AntLayout>

      <ChangePasswordModal open={passwordModalOpen} onClose={() => setPasswordModalOpen(false)} />
    </AntLayout>
  );
};

export default Layout;
