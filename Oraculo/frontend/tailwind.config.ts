import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Oraculo color palette
        'primary': {
          dark: '#1E293B',    // Azul Escuro - fundo principal
          light: '#3B82F6',   // Azul Claro - destaque/botões
        },
        'neutral': {
          gray: '#64748B',    // Cinza - textos secundários
          offwhite: '#F1F5F9', // OffWhite - textos claros
        },
        // Semantic aliases
        'chat-bg': '#1E293B',
        'chat-sidebar': '#0F172A',
        'chat-input': '#334155',
        'chat-hover': '#475569',
        'chat-border': 'rgba(59, 130, 246, 0.3)',
        'chat-text': '#F1F5F9',
        'chat-text-secondary': '#64748B',
        'chat-accent': '#3B82F6',
      },
      maxWidth: {
        'chat': '768px',
      },
      borderRadius: {
        'pill': '26px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(59, 130, 246, 0.3)',
        'glow-sm': '0 0 10px rgba(59, 130, 246, 0.2)',
      }
    },
  },
  plugins: [],
}
export default config
