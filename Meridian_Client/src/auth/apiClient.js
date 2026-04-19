const REFRESH_KEY = 'meridian.refresh'
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

function resolveUrl(path) {
  if (/^https?:\/\//i.test(path)) return path
  return `${API_BASE}${path}`
}

export const tokenStore = {
  get access() {
    return this._access
  },
  setAccess(token) {
    this._access = token || null
  },
  getRefresh() {
    return sessionStorage.getItem(REFRESH_KEY)
  },
  setRefresh(token) {
    if (token) sessionStorage.setItem(REFRESH_KEY, token)
    else sessionStorage.removeItem(REFRESH_KEY)
  },
  clear() {
    this._access = null
    sessionStorage.removeItem(REFRESH_KEY)
  },
  _access: null,
}

async function parse(response) {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export class ApiError extends Error {
  constructor(status, body) {
    const detail =
      (body && typeof body === 'object' && body.detail) ||
      (typeof body === 'string' && body) ||
      `Request failed (${status})`
    super(Array.isArray(detail) ? detail.map((d) => d.msg).join(', ') : detail)
    this.status = status
    this.body = body
  }
}

async function rawFetch(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && tokenStore.access) {
    headers.Authorization = `Bearer ${tokenStore.access}`
  }
  const res = await fetch(resolveUrl(path), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const parsed = await parse(res)
  if (!res.ok) throw new ApiError(res.status, parsed)
  return parsed
}

async function tryRefresh() {
  const refreshToken = tokenStore.getRefresh()
  if (!refreshToken) return false
  try {
    const data = await rawFetch('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    })
    tokenStore.setAccess(data.access_token)
    return true
  } catch {
    tokenStore.clear()
    return false
  }
}

export async function apiFetch(path, opts = {}) {
  try {
    return await rawFetch(path, { ...opts, auth: true })
  } catch (err) {
    if (err instanceof ApiError && err.status === 401 && opts._retry !== true) {
      const ok = await tryRefresh()
      if (ok) return rawFetch(path, { ...opts, auth: true })
    }
    throw err
  }
}

export const publicFetch = (path, opts = {}) => rawFetch(path, opts)
