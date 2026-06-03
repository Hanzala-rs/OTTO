'use client'
import { Play, Pause } from 'lucide-react'
import { useState, useRef, useEffect, useCallback } from 'react'

interface Props {
  audioUrl: string
  isOutgoing?: boolean
}

export default function AudioPlayer({ audioUrl, isOutgoing = false }: Props) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    const audio = new Audio(audioUrl)
    audioRef.current = audio
    audio.onloadedmetadata = () => setDuration(audio.duration)
    audio.ontimeupdate = () => setProgress(audio.currentTime / (audio.duration || 1))
    audio.onended = () => { setIsPlaying(false); setProgress(0) }
    return () => { audio.pause(); audio.src = '' }
  }, [audioUrl])

  const toggle = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) { audio.pause(); setIsPlaying(false) }
    else { audio.play(); setIsPlaying(true) }
  }, [isPlaying])

  const fmt = (s: number) => `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`

  const barColor = isOutgoing ? 'rgba(255,255,255,0.7)' : 'var(--chat-header)'
  const activeColor = isOutgoing ? '#fff' : 'var(--chat-header)'
  const btnBg = isOutgoing ? 'rgba(255,255,255,0.25)' : 'var(--chat-header)'

  return (
    <div className="flex items-center gap-2 py-1 min-w-[180px]">
      {/* Play/Pause button */}
      <button
        onClick={toggle}
        className="flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-full text-white transition hover:opacity-80"
        style={{ backgroundColor: btnBg }}
      >
        {isPlaying ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
      </button>

      {/* Waveform */}
      <div className="flex flex-1 items-end gap-[2px] h-8">
        {Array.from({ length: 28 }).map((_, i) => {
          const height = 4 + ((i * 13 + i * i) % 22)
          const filled = i / 28 <= progress
          return (
            <span
              key={i}
              className="rounded-full flex-1 transition-all duration-100"
              style={{
                height: `${height}px`,
                backgroundColor: filled ? activeColor : barColor,
                opacity: filled ? 1 : 0.5,
              }}
            />
          )
        })}
      </div>

      {/* Duration */}
      <span className="flex-shrink-0 text-[11px] opacity-70 tabular-nums">
        {fmt(duration)}
      </span>
    </div>
  )
}
