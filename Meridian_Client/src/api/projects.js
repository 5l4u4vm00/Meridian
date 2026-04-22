import { apiFetch } from '../auth/apiClient'

export const listProjects = () => apiFetch('/projects')

export const createProject = (payload) =>
  apiFetch('/projects', { method: 'POST', body: payload })

export const getProject = (code) => apiFetch(`/projects/${code}`)

export const updateProject = (code, payload) =>
  apiFetch(`/projects/${code}`, { method: 'PATCH', body: payload })
