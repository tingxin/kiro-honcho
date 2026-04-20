import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Accounts from './pages/Accounts'
import Subscriptions from './pages/Subscriptions'
import AccountLogs from './pages/AccountLogs'
import SystemUsers from './pages/SystemUsers'
import './App.css'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="accounts" element={<Accounts />} />
          <Route path="accounts/:accountId/subscriptions" element={<Subscriptions />} />
          <Route path="accounts/:accountId/logs" element={<AccountLogs />} />
          <Route path="system-users" element={<SystemUsers />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
