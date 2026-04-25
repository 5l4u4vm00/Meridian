import { useEffect, useRef, useState } from 'react'
import { Paperclip, X } from 'lucide-react'
import { getTaskDetail, updateTask } from '../../api/tasks'
import { createComment } from '../../api/comments'
import { createAttachment, downloadAttachment } from '../../api/attachments'

function relativeTime(iso) {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  const delta = Math.max(0, Date.now() - t)
  const s = Math.floor(delta / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}d`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

export default function TaskDrawer({ taskId, onClose, onChanged }) {
  const [task, setTask] = useState(null)
  const [comments, setComments] = useState([])
  const [attachments, setAttachments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [draftBody, setDraftBody] = useState('')
  const [descDraft, setDescDraft] = useState('')
  const [posting, setPosting] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (taskId == null) return
    let cancelled = false
    getTaskDetail(taskId)
      .then((detail) => {
        if (cancelled) return
        setTask(detail.task)
        setComments(detail.comments)
        setAttachments(detail.attachments)
        setDescDraft(detail.task.description || '')
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e.message || 'Failed to load')
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [taskId])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const saveDescription = async () => {
    if (!task) return
    if (descDraft === (task.description || '')) return
    try {
      const updated = await updateTask(task.id, { description: descDraft })
      setTask(updated)
      onChanged?.()
    } catch (e) {
      setError(e.message || 'Failed to save description')
    }
  }

  const submitComment = async (e) => {
    e.preventDefault()
    const body = draftBody.trim()
    if (!body || posting) return
    setPosting(true)
    try {
      const created = await createComment(task.id, body)
      setComments((prev) => [...prev, created])
      setDraftBody('')
      onChanged?.()
    } catch (e) {
      setError(e.message || 'Failed to post comment')
    } finally {
      setPosting(false)
    }
  }

  const onFilePicked = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !task) return
    try {
      const created = await createAttachment(task.id, file)
      setAttachments((prev) => [...prev, created])
      onChanged?.()
    } catch (err) {
      setError(err.message || 'Failed to add attachment')
    }
  }

  const onAttachmentClick = async (att) => {
    try {
      await downloadAttachment(att.id, att.filename)
    } catch (err) {
      setError(err.message || 'Failed to download attachment')
    }
  }

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <div className="drawer-code">{task?.code || ''}</div>
            <div className="drawer-title">{task?.title || (loading ? 'Loading…' : '')}</div>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={16} strokeWidth={1.5} />
          </button>
        </div>

        {error && <div className="drawer-error">{error}</div>}

        <div className="drawer-body">
          <section className="drawer-section">
            <div className="drawer-section-label">Description</div>
            <textarea
              className="drawer-desc"
              value={descDraft}
              placeholder="Add a description…"
              onChange={(e) => setDescDraft(e.target.value)}
              onBlur={saveDescription}
              rows={4}
            />
          </section>

          <section className="drawer-section">
            <div className="drawer-section-label">
              Comments ({comments.length})
            </div>
            <ul className="comment-list">
              {comments.map((c) => (
                <li key={c.id} className="comment-item">
                  <div className="avatar" style={{ width: 24, height: 24, fontSize: 10 }}>
                    {c.author_initials || '?'}
                  </div>
                  <div className="comment-body">
                    <div className="comment-meta">
                      <span className="comment-author">{c.author_name || 'Unknown'}</span>
                      <span className="comment-time">{relativeTime(c.created_at)}</span>
                    </div>
                    <div className="comment-text">{c.body}</div>
                  </div>
                </li>
              ))}
              {comments.length === 0 && !loading && (
                <li className="comment-empty">No comments yet.</li>
              )}
            </ul>
            <form className="comment-composer" onSubmit={submitComment}>
              <textarea
                value={draftBody}
                onChange={(e) => setDraftBody(e.target.value)}
                placeholder="Write a comment…"
                rows={2}
              />
              <button type="submit" disabled={posting || !draftBody.trim()}>
                {posting ? 'Posting…' : 'Post'}
              </button>
            </form>
          </section>

          <section className="drawer-section">
            <div className="drawer-section-label">
              Attachments ({attachments.length})
            </div>
            <ul className="attachment-list">
              {attachments.map((a) => (
                <li key={a.id} className="attachment-row">
                  <Paperclip size={12} strokeWidth={1.5} />
                  <button
                    type="button"
                    className="attachment-name"
                    onClick={() => onAttachmentClick(a)}
                  >
                    {a.filename}
                  </button>
                  <span className="attachment-meta">
                    {a.uploader_initials || '?'} · {relativeTime(a.created_at)}
                  </span>
                </li>
              ))}
              {attachments.length === 0 && !loading && (
                <li className="attachment-empty">No attachments yet.</li>
              )}
            </ul>
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: 'none' }}
              onChange={onFilePicked}
            />
            <button
              className="attachment-add"
              onClick={() => fileInputRef.current?.click()}
            >
              + Add attachment
            </button>
          </section>
        </div>
      </aside>
    </div>
  )
}
