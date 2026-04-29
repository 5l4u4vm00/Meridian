import { apiFetch } from '../auth/apiClient'

export const listBoard = (code) => apiFetch(`/projects/${code}/tasks`)

export const listMyTasks = (includeShipped = false) =>
  apiFetch(`/my-tasks?include_shipped=${includeShipped ? 'true' : 'false'}`)

export const getTaskDetail = (id) => apiFetch(`/tasks/${id}/detail`)

export const createTask = (code, payload) =>
  apiFetch(`/projects/${code}/tasks`, { method: 'POST', body: payload })

export const updateTask = (id, payload) =>
  apiFetch(`/tasks/${id}`, { method: 'PATCH', body: payload })

export const moveTask = (id, payload) =>
  apiFetch(`/tasks/${id}/move`, { method: 'POST', body: payload })
