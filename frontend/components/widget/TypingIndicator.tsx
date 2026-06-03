'use client'

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full animate-bounce"
          style={{
            backgroundColor: 'var(--chat-header)',
            opacity: 0.7,
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
    </div>
  )
}
