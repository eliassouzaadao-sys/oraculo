'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="max-w-chat mx-auto">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleSubmit()
        }}
        className="flex items-end gap-3 bg-chat-input border border-chat-border rounded-2xl p-2 shadow-lg hover:border-chat-accent/50 transition-colors focus-within:border-chat-accent focus-within:shadow-glow-sm"
        role="search"
      >
        <label htmlFor="chat-input" className="sr-only">
          Digite sua mensagem
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || "Envie uma mensagem..."}
          disabled={disabled}
          rows={1}
          aria-label="Digite sua mensagem para o Oraculo"
          aria-describedby="input-help"
          className="flex-1 bg-transparent text-chat-text placeholder:text-chat-text-secondary outline-none resize-none px-3 py-2.5 max-h-[200px]"
        />
        <span id="input-help" className="sr-only">
          Pressione Enter para enviar, Shift+Enter para nova linha
        </span>
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          aria-label={disabled ? 'Envio desabilitado' : 'Enviar mensagem'}
          className="flex-shrink-0 w-10 h-10 gradient-accent rounded-xl flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:opacity-90 hover:shadow-glow-sm focus:ring-2 focus:ring-chat-accent focus:ring-offset-2 focus:ring-offset-chat-bg"
        >
          <Send size={18} className="text-white" aria-hidden="true" />
        </button>
      </form>
    </div>
  )
}
