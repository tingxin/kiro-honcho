import React from 'react';
import { Row, Col, Card, Statistic, Spin } from 'antd';
import { UserOutlined, CloudServerOutlined, SafetyCertificateOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import styles from './Dashboard.module.css';
import { useAccountStore } from '../../stores/accountStore';
import { accountService } from '../../services/accounts';

interface DashboardStats {
  total_users: number;
  subscribed_users: number;
  active_subscriptions: number;
  total_accounts: number;
  active_accounts: number;
}

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { currentAccount } = useAccountStore();
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const data = await accountService.getStats(currentAccount?.id);
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [currentAccount]);

  if (loading && !stats) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      <Row gutter={[24, 24]} className={styles.statsRow}>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>{t('dashboard.icUsers')}</span>}
              value={stats?.total_users ?? 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>{t('dashboard.subscribedUsers')}</span>}
              value={stats?.subscribed_users ?? 0}
              prefix={<SafetyCertificateOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>{t('dashboard.activeSubscriptions')}</span>}
              value={stats?.active_subscriptions ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>{t('dashboard.awsAccounts')}</span>}
              value={`${stats?.active_accounts ?? 0} / ${stats?.total_accounts ?? 0}`}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
