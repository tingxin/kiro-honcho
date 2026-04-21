import React, { useState, useMemo } from 'react';
import { Layout as AntLayout, Menu, Dropdown, Avatar, Space, Spin, Button, Drawer, Modal, Input, message } from 'antd';
import {
  UserOutlined, LogoutOutlined, DownOutlined,
  CloudServerOutlined, KeyOutlined, SafetyCertificateOutlined,
  FileTextOutlined, DashboardOutlined, MenuOutlined,
} from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useAccountStore } from '../../stores/accountStore';
import { authService } from '../../services';
import { useTranslation } from 'react-i18next';
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
  const { t, i18n } = useTranslation();
  const { accounts, currentAccount, isLoading, fetchAccounts, setCurrentAccount } = useAccountStore();
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [mfaModalOpen, setMfaModalOpen] = useState(false);
  const [mfaData, setMfaData] = useState<{ qr_code: string; secret: string } | null>(null);
  const [mfaCode, setMfaCode] = useState('');

  React.useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // 未启用 MFA 时弹出提醒（可关闭，仅一次）
  const mfaReminderRef = React.useRef(false);
  React.useEffect(() => {
    if (user && !user.mfa_enabled && !mfaReminderRef.current) {
      mfaReminderRef.current = true;
      Modal.warning({
        title: t('mfa.reminder'),
        content: t('mfa.reminderContent'),
        okText: t('mfa.understood'),
      });
    }
  }, [user]);

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
    { key: '/dashboard', icon: <DashboardOutlined />, label: t('nav.dashboard') },
    { key: '/accounts', icon: <CloudServerOutlined />, label: t('nav.accounts') },
    ...(accountId
      ? [
        { key: `/accounts/${accountId}/subscriptions`, icon: <SafetyCertificateOutlined />, label: t('nav.subscriptions') },
        { key: `/accounts/${accountId}/logs`, icon: <FileTextOutlined />, label: t('nav.logs') },
      ]
      : []),
  ], [accountId, t]);

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

  const handleSetupMfa = async () => {
    try {
      const data = await authService.setupMfa();
      setMfaData(data);
      setMfaModalOpen(true);
    } catch { /* ignore */ }
  };

  const handleVerifyMfa = async () => {
    const success = await authService.verifyMfa(mfaCode);
    if (success) {
      setMfaModalOpen(false);
      setMfaCode('');
      setMfaData(null);
      // Refresh user data to update mfa_enabled
      const me = await authService.getCurrentUser();
      useAuthStore.getState().login(
        useAuthStore.getState().accessToken!,
        useAuthStore.getState().refreshToken!,
        me
      );
      message.success('MFA 已启用');
    } else {
      message.error('验证码错误，请重试');
    }
  };

  const handleDisableMfa = async () => {
    await authService.disableMfa();
    const me = await authService.getCurrentUser();
    useAuthStore.getState().login(
      useAuthStore.getState().accessToken!,
      useAuthStore.getState().refreshToken!,
      me
    );
  };

  const userMenuItems = [
    { key: 'changePassword', icon: <KeyOutlined />, label: t('nav.changePassword'), onClick: () => setPasswordModalOpen(true) },
    {
      key: 'mfa',
      icon: <SafetyCertificateOutlined />,
      label: user?.mfa_enabled ? t('nav.disableMfa') : t('nav.enableMfa'),
      onClick: user?.mfa_enabled ? handleDisableMfa : handleSetupMfa,
    },
    ...(user?.is_admin ? [{ key: 'systemUsers', icon: <UserOutlined />, label: t('nav.systemUsers'), onClick: () => navigate('/system-users') }] : []),
    { type: 'divider' as const },
    {
      key: 'lang',
      icon: <span>🌐</span>,
      label: i18n.language === 'zh' ? '中文' : i18n.language === 'de' ? 'Deutsch' : 'English',
      children: [
        { key: 'lang-zh', label: '中文', onClick: () => { i18n.changeLanguage('zh'); localStorage.setItem('kiro-lang', 'zh'); } },
        { key: 'lang-en', label: 'English', onClick: () => { i18n.changeLanguage('en'); localStorage.setItem('kiro-lang', 'en'); } },
        { key: 'lang-de', label: 'Deutsch', onClick: () => { i18n.changeLanguage('de'); localStorage.setItem('kiro-lang', 'de'); } },
      ],
    },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: t('nav.logout'), onClick: handleLogout },
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

      {/* MFA Setup Modal */}
      <Modal
        title={t('mfa.setupTitle')} open={mfaModalOpen}
        closable
        maskClosable={false}
        onCancel={() => { setMfaModalOpen(false); setMfaCode(''); setMfaData(null); }}
        footer={null}
        width={400}
      >
        {mfaData && (
          <div style={{ textAlign: 'center' }}>
            <p>{t('mfa.scanQr')}</p>
            <img src={mfaData.qr_code} alt="QR Code" style={{ width: 200, height: 200, margin: '16px auto' }} />
            <p style={{ fontSize: 12, color: '#888', wordBreak: 'break-all' }}>
              {t('mfa.manualKey')}: <code>{mfaData.secret}</code>
            </p>
            <Input
              placeholder={t('mfa.enterCode')}
              maxLength={6}
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
              style={{ textAlign: 'center', fontSize: 20, letterSpacing: 6, marginTop: 16 }}
              onPressEnter={handleVerifyMfa}
            />
            <Button type="primary" block style={{ marginTop: 12 }}
              onClick={handleVerifyMfa} disabled={mfaCode.length !== 6}>
              {t('mfa.verifyEnable')}
            </Button>
          </div>
        )}
      </Modal>
    </AntLayout>
  );
};

export default Layout;
