'use client'
import { useState, useCallback } from 'react'
import { sendTextMessage, sendVoiceMessage } from '@/lib/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  language: string
  audioUrl?: string
  timestamp: Date
  isVoice?: boolean
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'intro',
      role: 'assistant',
      content: "Assalam o Alaikum! I'm OTTO. How can I help you today?",
      language: 'en',
      timestamp: new Date(),
    }
  ])
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [
      ...prev,
      { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
    ])
  }

  const sendText = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return
    setError(null)
    addMessage({ role: 'user', content: text, language: 'en' })
    setIsLoading(true)
    try {
      const res = await sendTextMessage(text, sessionId)
      if (!sessionId) setSessionId(res.session_id)
      addMessage({
        role: 'assistant',
        content: res.response,
        language: res.language,
      })
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, isLoading])

  const sendVoice = useCallback(async (audioBlob: Blob) => {
    if (isLoading) return
    setError(null)
    setIsLoading(true)

    // Show user's voice bubble immediately before API call
    const userAudioUrl = URL.createObjectURL(audioBlob)
    addMessage({
      role: 'user',
      content: '',
      language: 'en',
      audioUrl: userAudioUrl,
      isVoice: true,
    })

    try {
      const res = await sendVoiceMessage(audioBlob, sessionId)
      if (!sessionId) setSessionId(res.sessionId)

      // Assistant audio + text response
      const audioUrl = URL.createObjectURL(res.audioBlob)
      addMessage({
        role: 'assistant',
        content: res.response,
        language: res.language,
        audioUrl,
        isVoice: true,
      })
    } catch (err: any) {
      setError(err.message || 'Voice processing failed')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, isLoading])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
    setError(null)
  }, [])

  return { messages, isLoading, error, sendText, sendVoice, clearChat, sessionId }
}
