import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined, CloudServerOutlined, SafetyOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authService } from '../../services'
import styles from './Login.module.css'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [mfaStep, setMfaStep] = useState(false)
  const [mfaUserId, setMfaUserId] = useState<number | null>(null)
  const [mfaCode, setMfaCode] = useState('')
  const navigate = useNavigate()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const result = await authService.login(values.username, values.password)
      if (result === 'mfa_required') {
        // handled inside authService, it sets mfaUserId
        return
      }
      if (result) {
        message.success('Login successful!')
        navigate('/dashboard')
      } else {
        message.error('Invalid username or password')
      }
    } catch (error: any) {
      if (error.mfa_required) {
        setMfaStep(true)
        setMfaUserId(error.user_id)
      } else {
        message.error('Login failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const onMfaSubmit = async () => {
    if (!mfaUserId || !mfaCode) return
    setLoading(true)
    try {
      const success = await authService.loginWithMfa(mfaUserId, mfaCode)
      if (success) {
        message.success('Login successful!')
        navigate('/dashboard')
      } else {
        message.error('Invalid TOTP code')
      }
    } catch {
      message.error('MFA verification failed')
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

        {!mfaStep ? (
          <Form name="login" onFinish={onFinish} autoComplete="off" layout="vertical" size="large">
            <Form.Item name="username" rules={[{ required: true, message: 'Please input your username!' }]}>
              <Input prefix={<UserOutlined />} placeholder="Username" />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: 'Please input your password!' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="Password" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>Login</Button>
            </Form.Item>
          </Form>
        ) : (
          <div>
            <p style={{ textAlign: 'center', marginBottom: 16, color: '#666' }}>
              请输入 Authenticator App 中的 6 位验证码
            </p>
            <Input
              prefix={<SafetyOutlined />}
              placeholder="000000"
              maxLength={6}
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
              size="large"
              style={{ textAlign: 'center', fontSize: 24, letterSpacing: 8 }}
              onPressEnter={onMfaSubmit}
            />
            <Button
              type="primary"
              loading={loading}
              block
              style={{ marginTop: 16 }}
              onClick={onMfaSubmit}
              disabled={mfaCode.length !== 6}
            >
              验证
            </Button>
            <Button type="link" block style={{ marginTop: 8 }} onClick={() => { setMfaStep(false); setMfaCode(''); }}>
              返回登录
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
