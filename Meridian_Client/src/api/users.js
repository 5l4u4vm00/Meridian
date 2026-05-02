import { apiFetch } from '../auth/apiClient'

export const listUsers = () => apiFetch('/users')
