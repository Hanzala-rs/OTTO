'use client'
import { useState } from 'react'
import { MessageCircle, X } from 'lucide-react'
import ChatWindow from './ChatWindow'

export default function ChatWidget() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-3 z-50 chat-slide-up sm:bottom-24 sm:right-6">
          <div className="flex h-[min(640px,80dvh)] w-[min(22rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-slate-200 shadow-2xl sm:w-96">
            <ChatWindow onClose={() => setOpen(false)} />
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
        className="fixed bottom-3 right-3 z-50 flex h-12 w-12 items-center justify-center rounded-full text-white shadow-xl transition hover:scale-105 hover:opacity-90 sm:bottom-6 sm:right-6 sm:h-14 sm:w-14"
        style={{ backgroundColor: 'var(--chat-header)' }}
      >
        {open ? (
          <X className="h-5 w-5 sm:h-6 sm:w-6" />
        ) : (
          <MessageCircle className="h-5 w-5 sm:h-6 sm:w-6" />
        )}
      </button>
    </>
  )
}
