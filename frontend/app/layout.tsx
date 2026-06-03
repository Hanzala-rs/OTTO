import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OTTO — Multilingual RAG Assistant',
  description: 'Ask anything in English or Urdu',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased" style={{ backgroundColor: 'var(--chat-bg)' }}>{children}</body>
    </html>
  )
}
