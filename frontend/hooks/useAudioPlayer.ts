'use client'
import { useState, useRef, useCallback } from 'react'

export function useAudioPlayer(audioUrl: string) {
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const play = useCallback(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl)
      audioRef.current.onended = () => setIsPlaying(false)
    }
    audioRef.current.play()
    setIsPlaying(true)
  }, [audioUrl])

  const pause = useCallback(() => {
    audioRef.current?.pause()
    setIsPlaying(false)
  }, [])

  const toggle = useCallback(() => {
    isPlaying ? pause() : play()
  }, [isPlaying, play, pause])

  return { isPlaying, toggle, play, pause }
}
