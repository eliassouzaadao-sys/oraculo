'use client'

import { useState } from 'react'
import { User, Sparkles, Copy, Check } from 'lucide-react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
// @ts-ignore - type issues with react-syntax-highlighter styles
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

interface Source {
  name: string
  score?: number
  excerpt?: string
}

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  isLoading?: boolean
  sources?: Source[]
}

export default function ChatMessage({ role, content, isLoading, sources }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`group flex gap-4 py-6 ${role === 'user' ? 'justify-end' : ''}`}
    >
      {role === 'assistant' && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl gradient-accent flex items-center justify-center shadow-glow-sm">
          <Sparkles size={18} className="text-white" />
        </div>
      )}

      <div
        className={`
          relative
          ${role === 'user'
            ? 'bg-chat-accent/20 border border-chat-accent/30 rounded-2xl rounded-tr-sm px-5 py-3 max-w-[70%]'
            : 'flex-1 max-w-[calc(100%-3.5rem)]'
          }
        `}
      >
        {/* Botao copiar - apenas para mensagens do assistente */}
        {role === 'assistant' && content && !isLoading && (
          <button
            onClick={handleCopy}
            className="absolute -top-2 right-0 p-1.5 rounded-lg bg-chat-input/80 border border-chat-border
                       opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-chat-hover"
            aria-label={copied ? 'Copiado!' : 'Copiar resposta'}
          >
            {copied ? (
              <Check size={14} className="text-green-400" />
            ) : (
              <Copy size={14} className="text-chat-text-secondary" />
            )}
          </button>
        )}

        <div className="chat-content text-chat-text">
          {role === 'assistant' && content ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const isInline = !match && !String(children).includes('\n')

                  return !isInline && match ? (
                    <div className="relative group/code my-4">
                      <div className="absolute top-2 right-2 text-xs text-chat-text-secondary bg-chat-bg/50 px-2 py-0.5 rounded">
                        {match[1]}
                      </div>
                      <SyntaxHighlighter
                        style={oneDark as { [key: string]: React.CSSProperties }}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-xl !bg-[#1a1a2e] !mt-0"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className="bg-chat-input/50 px-1.5 py-0.5 rounded text-sm font-mono text-chat-accent" {...props}>
                      {children}
                    </code>
                  )
                },
                p({ children }) {
                  return <p className="mb-4 last:mb-0 leading-relaxed">{children}</p>
                },
                ul({ children }) {
                  return <ul className="mb-4 ml-4 list-disc space-y-2">{children}</ul>
                },
                ol({ children }) {
                  return <ol className="mb-4 ml-4 list-decimal space-y-2">{children}</ol>
                },
                li({ children }) {
                  return <li className="leading-relaxed">{children}</li>
                },
                h1({ children }) {
                  return <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>
                },
                h2({ children }) {
                  return <h2 className="text-xl font-bold mb-3 mt-5 first:mt-0">{children}</h2>
                },
                h3({ children }) {
                  return <h3 className="text-lg font-semibold mb-2 mt-4 first:mt-0">{children}</h3>
                },
                blockquote({ children }) {
                  return (
                    <blockquote className="border-l-4 border-chat-accent/50 pl-4 my-4 italic text-chat-text-secondary">
                      {children}
                    </blockquote>
                  )
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-4">
                      <table className="w-full border-collapse border border-chat-border rounded-lg">
                        {children}
                      </table>
                    </div>
                  )
                },
                thead({ children }) {
                  return <thead className="bg-chat-input/50">{children}</thead>
                },
                th({ children }) {
                  return (
                    <th className="border border-chat-border px-4 py-2 text-left font-semibold">
                      {children}
                    </th>
                  )
                },
                td({ children }) {
                  return <td className="border border-chat-border px-4 py-2">{children}</td>
                },
                a({ href, children }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-chat-accent hover:underline"
                    >
                      {children}
                    </a>
                  )
                },
                hr() {
                  return <hr className="my-6 border-chat-border" />
                },
              }}
            >
              {content}
            </ReactMarkdown>
          ) : (
            <span className="whitespace-pre-wrap">{content}</span>
          )}

          {isLoading && !content && (
            <span className="inline-flex gap-1.5 py-1">
              <span className="w-2 h-2 bg-chat-accent rounded-full animate-bounce-delay-1" />
              <span className="w-2 h-2 bg-chat-accent rounded-full animate-bounce-delay-2" />
              <span className="w-2 h-2 bg-chat-accent rounded-full animate-bounce-delay-3" />
            </span>
          )}
          {isLoading && content && (
            <span className="cursor-blink ml-0.5">|</span>
          )}
        </div>

        {/* Citacoes/Fontes */}
        {role === 'assistant' && sources && sources.length > 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.3 }}
            className="mt-4 pt-4 border-t border-chat-border/50"
          >
            <p className="text-xs text-chat-text-secondary mb-2 font-medium">Fontes consultadas:</p>
            <div className="flex flex-wrap gap-2">
              {sources.map((source, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 text-xs bg-chat-input/50 border border-chat-border
                             px-2.5 py-1 rounded-full text-chat-text-secondary hover:text-chat-text
                             hover:border-chat-accent/50 transition-colors cursor-default"
                  title={source.excerpt || source.name}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-chat-accent" />
                  {source.name}
                  {source.score && (
                    <span className="text-chat-accent/70">
                      {Math.round(source.score * 100)}%
                    </span>
                  )}
                </span>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {role === 'user' && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-chat-input border border-chat-border flex items-center justify-center">
          <User size={18} className="text-chat-text" />
        </div>
      )}
    </motion.div>
  )
}
