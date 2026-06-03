'use client'
import { Play, Pause } from 'lucide-react'
import { useAudioPlayer } from '@/hooks/useAudioPlayer'

export default function AudioPlayer({ audioUrl }: { audioUrl: string }) {
  const { isPlaying, toggle } = useAudioPlayer(audioUrl)

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 transition-colors text-white text-sm"
    >
      {isPlaying ? <Pause size={14} /> : <Play size={14} />}
      <span>{isPlaying ? 'Pause' : 'Play response'}</span>
    </button>
  )
}
