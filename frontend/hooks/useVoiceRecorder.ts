'use client'
import { useState, useRef, useCallback } from 'react'

export type RecordingState = 'idle' | 'recording' | 'processing'

export function useVoiceRecorder(onComplete: (blob: Blob) => void) {
  const [state, setState] = useState<RecordingState>('idle')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
        ? 'audio/ogg;codecs=opus'
        : 'audio/webm;codecs=opus'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: mimeType })
        setState('processing')
        onComplete(blob)
      }

      recorder.start(100)
      setState('recording')
    } catch {
      setState('idle')
      throw new Error('Microphone access denied')
    }
  }, [onComplete])

  const stop = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }, [])

  const reset = useCallback(() => setState('idle'), [])

  return { state, start, stop, reset }
}
