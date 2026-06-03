import ChatWidget from '@/components/widget/ChatWidget'

export default function Home() {
  return (
    <div className="relative min-h-screen" style={{ backgroundColor: 'var(--chat-bg)' }}>
      <div className="mx-auto flex max-w-3xl flex-col items-center px-4 py-12 text-center sm:px-6 sm:py-24">
        <span className="mb-4 rounded-full border border-slate-300 bg-white/60 px-3 py-1 text-[10px] font-medium uppercase tracking-widest text-slate-500 sm:text-xs">
          Always online · Never sleeps
        </span>
        <h1 className="text-4xl font-black tracking-tight text-slate-800 sm:text-6xl md:text-7xl">
          Talk to{' '}
          <span
            className="bg-clip-text text-transparent"
            style={{
              backgroundImage:
                'linear-gradient(to right, var(--chat-header), oklch(0.55 0.13 155), var(--chat-header))',
            }}
          >
            OTTO
          </span>
        </h1>
        <p className="mt-6 max-w-xl text-base text-slate-600 sm:text-lg">
          Your multilingual AI sidekick. Type in English or اردو, send a voice note — OTTO responds instantly.
        </p>
        <p
          className="mt-8 inline-flex items-center gap-2 text-xs font-medium sm:text-sm"
          style={{ color: 'var(--chat-header)' }}
        >
          <span
            className="h-2 w-2 animate-pulse rounded-full"
            style={{ backgroundColor: 'var(--chat-header)' }}
          />
          Tap the bubble bottom-right to start chatting →
        </p>
      </div>
      <ChatWidget />
    </div>
  )
}
