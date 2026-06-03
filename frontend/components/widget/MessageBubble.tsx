'use client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn, isUrdu, formatTime } from '@/lib/utils'
import AudioPlayer from './AudioPlayer'
import { CheckCheck } from 'lucide-react'
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
        className="relative max-w-[85%] rounded-lg px-3 py-2 text-sm shadow-sm"
        style={{
          backgroundColor: isUser ? 'var(--bubble-out)' : 'var(--bubble-in)',
          color: '#1a1a1a',
        }}
        dir={rtl ? 'rtl' : 'ltr'}
      >
        {/* Audio player — user sent (isOutgoing=true) or bot response (isOutgoing=false) */}
        {message.audioUrl && (
          <AudioPlayer audioUrl={message.audioUrl} isOutgoing={isUser} />
        )}

        {/* Markdown text content */}
        {message.content && !message.audioUrl && (
          <div className={cn('leading-relaxed break-words', rtl && 'urdu')}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h3: ({ children }) => <h3 className="font-semibold text-sm mt-2 mb-1">{children}</h3>,
                h4: ({ children }) => <h4 className="font-semibold text-xs mt-2 mb-1">{children}</h4>,
                p: ({ children }) => <p className="mb-1">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-1 space-y-0.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-1 space-y-0.5">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="text-xs border-collapse w-full">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead>{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-slate-200">{children}</tr>,
                th: ({ children }) => (
                  <th className="text-left px-2 py-1 font-semibold bg-slate-100 border border-slate-200">{children}</th>
                ),
                td: ({ children }) => (
                  <td className="px-2 py-1 border border-slate-200">{children}</td>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
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
