import { apiFetch } from '../auth/apiClient'

export const listAttachments = (taskId) => apiFetch(`/tasks/${taskId}/attachments`)

export const createAttachment = (taskId, file) => {
  const fd = new FormData()
  fd.append('file', file, file.name)
  return apiFetch(`/tasks/${taskId}/attachments`, { method: 'POST', body: fd })
}

export async function downloadAttachment(id, filename) {
  const res = await apiFetch(`/attachments/${id}/download`, { raw: true })
  const blob = await res.blob()
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename || 'download'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(objectUrl)
}
