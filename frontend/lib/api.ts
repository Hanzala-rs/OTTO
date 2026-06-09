const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatResponse {
  response: string
  session_id: string
  language: string
}

export async function sendTextMessage(
  message: string,
  sessionId?: string,
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export interface VoiceResponse {
  audioBlob: Blob
  sessionId: string
  transcript: string
  language: string
  response: string
}

export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId?: string,
): Promise<VoiceResponse> {
  if (audioBlob.size < 100) throw new Error('Recording too short')

  const form = new FormData()
  form.append('audio', audioBlob, 'recording.ogg')
  if (sessionId) form.append('session_id', sessionId)

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 60_000)

  const res = await fetch(`${API_URL}/voice`, {
    method: 'POST',
    body: form,
    signal: controller.signal,
  }).catch((err: any) => {
    clearTimeout(timeout)
    throw err.name === 'AbortError' ? new Error('Request timed out') : err
  })
  clearTimeout(timeout)

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  return {
    audioBlob: await res.blob(),
    sessionId: res.headers.get('X-Session-Id') || sessionId || '',
    transcript: decodeURIComponent(res.headers.get('X-Transcript') || ''),
    language: res.headers.get('X-Language') || 'en',
    response: decodeURIComponent(res.headers.get('X-Response') || ''),
  }
}
