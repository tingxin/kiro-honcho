import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { UserOutlined, CloudServerOutlined, DollarOutlined, TeamOutlined } from '@ant-design/icons';
import styles from './Dashboard.module.css';
import { useAccountStore } from '../../stores/accountStore';

const Dashboard: React.FC = () => {
  const { currentAccount } = useAccountStore();

  return (
    <div className={styles.dashboard}>
      <Row gutter={[24, 24]} className={styles.statsRow}>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>总用户数</span>}
              value={0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>活跃订阅</span>}
              value={0}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>本月 Credit</span>}
              value={0}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className={styles.statCard}>
            <Statistic
              title={<span className={styles.statTitle}>AWS 账号</span>}
              value={currentAccount ? 1 : 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
