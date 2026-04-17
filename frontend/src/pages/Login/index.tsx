import { useState } from 'react'
import { Form, Input, Button, Card, message, Space } from 'antd'
import { UserOutlined, LockOutlined, CloudServerOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authService } from '../../services'
import styles from './Login.module.css'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    
    try {
      const success = await authService.login(values.username, values.password)
      
      if (success) {
        message.success('Login successful!')
        navigate('/dashboard')
      } else {
        message.error('Invalid username or password')
      }
    } catch (error) {
      message.error('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <div className={styles.header}>
          <CloudServerOutlined className={styles.icon} />
          <h1>Kiro Honcho</h1>
          <p>Multi-AWS Account Management Platform</p>
        </div>
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please input your username!' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username (default: admin)"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password (default: admin123)"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              Login
            </Button>
          </Form.Item>
        </Form>

        <div className={styles.footer}>
          <Space direction="vertical" align="center" style={{ width: '100%' }}>
            <p className={styles.note}>
              Default credentials: <code>admin</code> / <code>admin123</code>
            </p>
          </Space>
        </div>
      </Card>
    </div>
  )
}
