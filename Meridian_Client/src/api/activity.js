import { apiFetch } from '../auth/apiClient'

export const getStats = (code) => apiFetch(`/projects/${code}/stats`)
export const getWorkload = (code) => apiFetch(`/projects/${code}/workload`)
export const getActivity = (code, limit = 20) =>
  apiFetch(`/projects/${code}/activity?limit=${limit}`)
