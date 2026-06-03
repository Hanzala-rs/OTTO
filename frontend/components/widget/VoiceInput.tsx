'use client'
import { Mic, MicOff, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder'

interface Props {
  onVoiceMessage: (blob: Blob) => void
  disabled?: boolean
}

export default function VoiceInput({ onVoiceMessage, disabled }: Props) {
  const { state, start, stop } = useVoiceRecorder((blob) => {
    onVoiceMessage(blob)
  })

  const handleClick = () => {
    if (state === 'recording') {
      stop()
    } else if (state === 'idle' && !disabled) {
      start()
    }
  }

  const isRecording = state === 'recording'
  const isProcessing = state === 'processing'

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled || isProcessing}
      title={isRecording ? 'Stop recording' : 'Record voice'}
      className={cn(
        'flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full text-white transition-all',
        isRecording && 'animate-pulse',
        (disabled || isProcessing) && 'opacity-40 cursor-not-allowed',
      )}
      style={{ backgroundColor: isRecording ? '#ef4444' : 'var(--chat-header)' }}
    >
      {isProcessing ? (
        <Loader2 size={18} className="animate-spin" />
      ) : isRecording ? (
        <MicOff size={18} />
      ) : (
        <Mic size={18} />
      )}
    </button>
  )
}
