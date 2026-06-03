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
        {/* Voice message — user side (no audio URL, show static waveform) */}
        {message.isVoice && isUser && !message.audioUrl && (
          <div className="flex items-center gap-2 py-1 min-w-[180px]">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-white/25">
              <Mic size={16} className="text-white" />
            </div>
            <div className="flex flex-1 items-end gap-[2px] h-8">
              {Array.from({ length: 28 }).map((_, i) => (
                <span
                  key={i}
                  className="rounded-full flex-1"
                  style={{ height: `${4 + ((i * 13 + i * i) % 22)}px`, backgroundColor: 'rgba(255,255,255,0.8)' }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Audio player for bot voice responses */}
        {message.audioUrl && (
          <AudioPlayer audioUrl={message.audioUrl} isOutgoing={isUser} />
        )}

        {/* Text content */}
        {message.content && !message.audioUrl && (
          <div className={cn('leading-relaxed break-words space-y-1', rtl && 'urdu')}>
            {message.content.split('\n').filter(l => l.trim()).map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        )}

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
