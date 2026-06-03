import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        otto: {
          primary: '#4F46E5',
          hover:   '#4338CA',
          bg:      '#0F172A',
          surface: '#1E293B',
          border:  '#334155',
          text:    '#F1F5F9',
          muted:   '#94A3B8',
        },
      },
      animation: {
        'bounce-slow': 'bounce 1.2s infinite',
      },
    },
  },
  plugins: [],
}

export default config
