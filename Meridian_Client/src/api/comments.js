import { apiFetch } from '../auth/apiClient'

export const listComments = (taskId) => apiFetch(`/tasks/${taskId}/comments`)

export const createComment = (taskId, body) =>
  apiFetch(`/tasks/${taskId}/comments`, { method: 'POST', body: { body } })
