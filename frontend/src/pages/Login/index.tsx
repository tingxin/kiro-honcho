import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined, CloudServerOutlined, SafetyOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { authService } from '../../services'
import styles from './Login.module.css'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [mfaStep, setMfaStep] = useState(false)
  const [mfaUserId, setMfaUserId] = useState<number | null>(null)
  const [mfaCode, setMfaCode] = useState('')
  const navigate = useNavigate()
  const { t } = useTranslation()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const result = await authService.login(values.username, values.password)
      if (result) {
        message.success(t('common.success'))
        navigate('/dashboard')
      } else {
        message.error(t('login.invalidCredentials'))
      }
    } catch (error: any) {
      if (error.mfa_required) {
        setMfaStep(true)
        setMfaUserId(error.user_id)
      } else {
        message.error(t('login.loginFailed'))
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
        message.success(t('common.success'))
        navigate('/dashboard')
      } else {
        message.error(t('login.mfaInvalid'))
      }
    } catch {
      message.error(t('login.loginFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <div className={styles.header}>
          <CloudServerOutlined className={styles.icon} />
          <h1>{t('login.title')}</h1>
          <p>{t('login.subtitle')}</p>
        </div>

        {!mfaStep ? (
          <Form name="login" onFinish={onFinish} autoComplete="off" layout="vertical" size="large">
            <Form.Item name="username" rules={[{ required: true, message: t('login.username') }]}>
              <Input prefix={<UserOutlined />} placeholder={t('login.username')} />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: t('login.password') }]}>
              <Input.Password prefix={<LockOutlined />} placeholder={t('login.password')} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>{t('login.login')}</Button>
            </Form.Item>
          </Form>
        ) : (
          <div>
            <p style={{ textAlign: 'center', marginBottom: 16, color: '#666' }}>{t('login.mfaHint')}</p>
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
            <Button type="primary" loading={loading} block style={{ marginTop: 16 }}
              onClick={onMfaSubmit} disabled={mfaCode.length !== 6}>
              {t('login.mfaVerify')}
            </Button>
            <Button type="link" block style={{ marginTop: 8 }}
              onClick={() => { setMfaStep(false); setMfaCode(''); }}>
              {t('login.mfaBack')}
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
