'use client'
import { useRef, useEffect, useState } from 'react'
import { Send, Trash2, ArrowLeft } from 'lucide-react'
import { useChat } from '@/hooks/useChat'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import VoiceInput from './VoiceInput'

interface Props {
  onClose?: () => void
}

export default function ChatWindow({ onClose }: Props) {
  const { messages, isLoading, error, sendText, sendVoice, clearChat } = useChat()
  const [input, setInput] = useState('')
  const [isVoiceBusy, setIsVoiceBusy] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const isBusy = isLoading || isVoiceBusy

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const t = input.trim()
    if (!t || isBusy) return
    sendText(t)
    setInput('')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center gap-3 px-3 py-3"
        style={{ backgroundColor: 'var(--chat-header)' }}
      >
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white transition-colors"
          aria-label="Close chat"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white font-semibold text-lg">
          O
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-white">OTTO</div>
          <div className="text-xs text-white/70">
            {isBusy ? 'typing…' : 'online · EN | اردو'}
          </div>
        </div>
        <button
          onClick={clearChat}
          title="Clear chat"
          className="text-white/60 hover:text-white transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 space-y-2 overflow-y-auto px-3 py-4 chat-scroll"
        style={{
          backgroundColor: 'var(--chat-bg)',
          backgroundImage:
            'radial-gradient(circle at 20% 10%, oklch(0.88 0.04 110) 0, transparent 40%), radial-gradient(circle at 80% 80%, oklch(0.9 0.05 130) 0, transparent 45%)',
        }}
      >
        {messages.length === 0 && (
          <p className="text-center text-slate-500 text-sm mt-8">
            Ask me anything in English or اردو
          </p>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isBusy && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-white px-3 py-2 shadow-sm">
              <TypingIndicator />
            </div>
          </div>
        )}
        {error && (
          <p className="text-center text-red-500 text-xs px-2">{error}</p>
        )}
      </div>

      {/* Composer */}
      <div
        className="flex items-center gap-2 px-2 py-2"
        style={{ backgroundColor: 'var(--composer-bg)' }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Type in English or اردو..."
          disabled={isBusy}
          className="flex-1 rounded-full bg-white px-4 py-2 text-sm text-slate-800 outline-none placeholder-slate-400 disabled:opacity-50"
          style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}
        />
        <VoiceInput onVoiceMessage={sendVoice} disabled={isLoading} onBusyChange={setIsVoiceBusy} />
        {input.trim() && (
          <button
            onClick={handleSend}
            disabled={isBusy}
            aria-label="Send message"
            className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full text-white transition hover:opacity-90 disabled:opacity-40"
            style={{ backgroundColor: 'var(--chat-header)' }}
          >
            <Send className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
}
