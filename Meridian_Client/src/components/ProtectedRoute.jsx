import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export default function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return <div className="auth-loading">Loading…</div>
  }
  if (status !== 'authed') {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <Outlet />
}
