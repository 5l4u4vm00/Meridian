import { X } from 'lucide-react'

export default function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <span className="serif modal-title">{title}</span>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={14} strokeWidth={1.5} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
