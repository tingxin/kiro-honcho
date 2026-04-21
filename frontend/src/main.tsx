import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import deDE from 'antd/locale/de_DE'
import App from './App'
import './i18n'
import './index.css'
import i18n from './i18n'

function getAntdLocale() {
  const lang = i18n.language || 'zh'
  if (lang.startsWith('en')) return enUS
  if (lang.startsWith('de')) return deDE
  return zhCN
}

function Root() {
  const [locale, setLocale] = React.useState(getAntdLocale())
  React.useEffect(() => {
    const handler = () => setLocale(getAntdLocale())
    i18n.on('languageChanged', handler)
    return () => i18n.off('languageChanged', handler)
  }, [])
  return (
    <ConfigProvider locale={locale} theme={{ token: { colorPrimary: '#1890ff', borderRadius: 6 } }}>
      <App />
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
)
