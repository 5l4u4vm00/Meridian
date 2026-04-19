import { createContext, useCallback, useEffect, useState } from 'react'
import { apiFetch, publicFetch, tokenStore } from './apiClient'

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // loading | anon | authed

  const loadMe = useCallback(async () => {
    const me = await apiFetch('/auth/me')
    setUser(me)
    setStatus('authed')
    return me
  }, [])

  const handleTokens = useCallback(
    async ({ access_token, refresh_token }) => {
      tokenStore.setAccess(access_token)
      if (refresh_token) tokenStore.setRefresh(refresh_token)
      await loadMe()
    },
    [loadMe],
  )

  useEffect(() => {
    let cancelled = false
    async function bootstrap() {
      const refreshToken = tokenStore.getRefresh()
      if (!refreshToken) {
        if (!cancelled) setStatus('anon')
        return
      }
      try {
        const data = await publicFetch('/auth/refresh', {
          method: 'POST',
          body: { refresh_token: refreshToken },
        })
        tokenStore.setAccess(data.access_token)
        await loadMe()
      } catch {
        tokenStore.clear()
        if (!cancelled) {
          setUser(null)
          setStatus('anon')
        }
      }
    }
    bootstrap()
    return () => {
      cancelled = true
    }
  }, [loadMe])

  const login = useCallback(
    async (email, password) => {
      const tokens = await publicFetch('/auth/login', {
        method: 'POST',
        body: { email, password },
      })
      await handleTokens(tokens)
    },
    [handleTokens],
  )

  const register = useCallback(
    async (email, password, name) => {
      const tokens = await publicFetch('/auth/register', {
        method: 'POST',
        body: { email, password, name },
      })
      await handleTokens(tokens)
    },
    [handleTokens],
  )

  const logout = useCallback(async () => {
    const refreshToken = tokenStore.getRefresh()
    if (refreshToken) {
      try {
        await publicFetch('/auth/logout', {
          method: 'POST',
          body: { refresh_token: refreshToken },
        })
      } catch {
        // ignore — clear client state regardless
      }
    }
    tokenStore.clear()
    setUser(null)
    setStatus('anon')
  }, [])

  const value = { user, status, login, register, logout }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
