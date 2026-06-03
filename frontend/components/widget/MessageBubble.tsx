'use client'
import { cn, isUrdu, formatTime } from '@/lib/utils'
import AudioPlayer from './AudioPlayer'
import { Mic, CheckCheck } from 'lucide-react'
import type { Message } from '@/hooks/useChat'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const rtl = isUrdu(message.content)

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className="relative max-w-[78%] rounded-lg px-3 py-2 text-sm shadow-sm"
        style={{
          backgroundColor: isUser ? 'var(--bubble-out)' : 'var(--bubble-in)',
          color: '#1a1a1a',
        }}
        dir={rtl ? 'rtl' : 'ltr'}
      >
        {/* Voice indicator */}
        {message.isVoice && (
          <span className="inline-flex items-center gap-1 text-xs text-slate-500 mb-1">
            <Mic size={10} />
            {isUser ? 'Voice message' : 'Voice response'}
          </span>
        )}

        {/* Text content */}
        {message.content && (
          <p className={cn('leading-relaxed whitespace-pre-wrap break-words', rtl && 'urdu')}>
            {message.content}
          </p>
        )}

        {/* Audio player for voice responses */}
        {message.audioUrl && <AudioPlayer audioUrl={message.audioUrl} />}

        {/* Timestamp + read receipt */}
        <div className="mt-1 flex items-center justify-end gap-1 text-[10px] text-slate-500">
          <span>{formatTime(message.timestamp)}</span>
          {isUser && (
            <CheckCheck className="h-3 w-3" style={{ color: 'var(--chat-header)' }} />
          )}
        </div>
      </div>
    </div>
  )
}
