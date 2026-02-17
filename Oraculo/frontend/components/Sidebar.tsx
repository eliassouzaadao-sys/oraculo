'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import Image from 'next/image'
import {
  Plus,
  Upload,
  Link,
  FileText,
  Settings,
  Trash2,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  MessageSquare,
  Download,
  Clock,
  MoreHorizontal,
  LogOut,
  User as UserIcon
} from 'lucide-react'
import { User } from '@/lib/auth'
import { Conversation, loadConversations, deleteConversation } from '@/lib/storage'
import { downloadConversation } from '@/lib/export'

interface Stats {
  total_documentos: number
  total_chunks: number
  fontes: string[]
}

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  onNewChat: () => void
  onUpload: (file: File) => Promise<boolean>
  onAddUrl: (url: string) => Promise<boolean>
  onClear: () => void
  onDeleteDocument?: (source: string) => Promise<boolean>
  onSelectConversation?: (conversation: Conversation) => void
  activeConversationId?: string | null
  stats: Stats
  user?: User | null
  onLogout?: () => void
}

export default function Sidebar({
  isOpen,
  onToggle,
  onNewChat,
  onUpload,
  onAddUrl,
  onClear,
  onDeleteDocument,
  onSelectConversation,
  activeConversationId,
  stats,
  user,
  onLogout
}: SidebarProps) {
  const [addDocOpen, setAddDocOpen] = useState(false)
  const [docsOpen, setDocsOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(true)
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [documentMenuOpen, setDocumentMenuOpen] = useState<string | null>(null)
  const [conversationMenuOpen, setConversationMenuOpen] = useState<string | null>(null)

  // Carrega conversas do localStorage
  useEffect(() => {
    setConversations(loadConversations())
  }, [activeConversationId])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploading(true)
      await onUpload(file)
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleAddUrl = async () => {
    if (url.trim()) {
      setUploading(true)
      await onAddUrl(url)
      setUrl('')
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (source: string) => {
    if (onDeleteDocument) {
      const success = await onDeleteDocument(source)
      if (success) {
        toast.success('Documento removido')
      }
    }
    setDocumentMenuOpen(null)
  }

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id)
    setConversations(loadConversations())
    toast.success('Conversa removida')
    setConversationMenuOpen(null)
  }

  const handleExportConversation = (conversation: Conversation) => {
    downloadConversation(conversation, 'md')
    toast.success('Conversa exportada')
    setConversationMenuOpen(null)
  }

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return 'Hoje'
    if (days === 1) return 'Ontem'
    if (days < 7) return `${days} dias atras`
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
  }

  const formatSource = (source: string) => {
    // YouTube URLs
    if (source.includes('youtube.com') || source.includes('youtu.be')) {
      const match = source.match(/(?:v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)
      if (match) {
        return `YouTube: ${match[1]}`
      }
      return 'YouTube Video'
    }

    // Other URLs - show domain
    if (source.startsWith('http://') || source.startsWith('https://')) {
      try {
        const url = new URL(source)
        return url.hostname.replace('www.', '')
      } catch {
        return source.substring(0, 30) + '...'
      }
    }

    // Files - show just filename
    return source
  }

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={onToggle}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-chat-sidebar text-chat-text hover:bg-chat-hover transition-colors"
        aria-label={isOpen ? 'Fechar menu' : 'Abrir menu'}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
          fixed lg:relative
          z-40
          w-72 h-full
          bg-chat-sidebar
          border-r border-chat-border
          flex flex-col
          transition-transform duration-300
        `}
      >
        {/* Header */}
        <div className="p-5 border-b border-chat-border">
          <h1 className="text-xl font-extrabold flex items-center gap-3 text-chat-text">
            <Image
              src="/logo-symbol.png"
              alt="Oraculo"
              width={32}
              height={32}
              className="w-8 h-8 object-contain"
            />
            Oraculo
          </h1>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-4">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl gradient-accent text-white font-medium hover:opacity-90 transition-all shadow-glow-sm hover:shadow-glow"
          >
            <Plus size={18} />
            Nova conversa
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4">
          {/* Stats Card */}
          <div className="mb-4 p-3 rounded-xl bg-primary-dark/50 border border-chat-border">
            <p className="text-chat-text-secondary text-sm flex items-center gap-2">
              <FileText size={16} className="text-chat-accent" />
              <span className="text-chat-text font-medium">{stats.total_documentos}</span> documento(s) na base
            </p>
          </div>

          {/* Conversation History */}
          {conversations.length > 0 && (
            <div className="mb-2">
              <button
                onClick={() => setHistoryOpen(!historyOpen)}
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-chat-hover transition-colors text-sm"
              >
                <span className="flex items-center gap-2 text-chat-text">
                  <Clock size={16} className="text-chat-accent" />
                  Historico
                </span>
                {historyOpen ? (
                  <ChevronDown size={16} className="text-chat-text-secondary" />
                ) : (
                  <ChevronRight size={16} className="text-chat-text-secondary" />
                )}
              </button>

              <AnimatePresence>
                {historyOpen && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 space-y-1 max-h-64 overflow-y-auto"
                  >
                    {conversations.map((conv) => (
                      <div
                        key={conv.id}
                        className={`
                          group relative flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer
                          transition-colors text-sm
                          ${activeConversationId === conv.id
                            ? 'bg-chat-accent/20 border border-chat-accent/30'
                            : 'hover:bg-chat-hover border border-transparent'
                          }
                        `}
                        onClick={() => onSelectConversation?.(conv)}
                      >
                        <MessageSquare size={14} className="text-chat-text-secondary flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-chat-text truncate text-xs">{conv.title}</p>
                          <p className="text-chat-text-secondary text-[10px]">{formatDate(conv.updatedAt)}</p>
                        </div>

                        {/* Menu de opcoes */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setConversationMenuOpen(conversationMenuOpen === conv.id ? null : conv.id)
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-chat-input transition-all"
                        >
                          <MoreHorizontal size={14} className="text-chat-text-secondary" />
                        </button>

                        {/* Dropdown menu */}
                        {conversationMenuOpen === conv.id && (
                          <div className="absolute right-0 top-full mt-1 z-50 bg-chat-input border border-chat-border rounded-lg shadow-lg py-1 min-w-[120px]">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleExportConversation(conv)
                              }}
                              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-chat-text hover:bg-chat-hover transition-colors"
                            >
                              <Download size={12} />
                              Exportar
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteConversation(conv.id)
                              }}
                              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 transition-colors"
                            >
                              <Trash2 size={12} />
                              Excluir
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Add Document */}
          <div className="mb-2">
            <button
              onClick={() => setAddDocOpen(!addDocOpen)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-chat-hover transition-colors text-sm"
            >
              <span className="flex items-center gap-2 text-chat-text">
                <Plus size={16} className="text-chat-accent" />
                Adicionar documento
              </span>
              {addDocOpen ? <ChevronDown size={16} className="text-chat-text-secondary" /> : <ChevronRight size={16} className="text-chat-text-secondary" />}
            </button>

            <AnimatePresence>
              {addDocOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 p-4 bg-primary-dark/50 border border-chat-border rounded-xl space-y-4"
                >
                  {/* File Upload */}
                  <label className="block">
                    <div className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-chat-accent/30 rounded-xl cursor-pointer hover:bg-chat-accent/10 hover:border-chat-accent/50 transition-all text-sm">
                      <Upload size={18} className="text-chat-accent" />
                      <span className="text-chat-text">
                        {uploading ? 'Enviando...' : 'Upload de arquivo'}
                      </span>
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.json,.png,.jpg,.jpeg"
                      onChange={handleFileChange}
                      disabled={uploading}
                    />
                  </label>

                  {/* URL */}
                  <div className="space-y-2">
                    <p className="text-xs text-chat-text-secondary">Ou adicione um link:</p>
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://..."
                        className="flex-1 min-w-0 px-3 py-2 bg-chat-input border border-chat-border rounded-lg text-sm text-chat-text placeholder:text-chat-text-secondary outline-none focus:border-chat-accent transition-colors"
                        onKeyDown={(e) => e.key === 'Enter' && handleAddUrl()}
                      />
                      <button
                        onClick={handleAddUrl}
                        disabled={uploading || !url.trim()}
                        className="flex-shrink-0 p-2 bg-chat-accent rounded-lg hover:bg-chat-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        <Link size={16} className="text-white" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Documents List */}
          {stats.fontes.length > 0 && (
            <div className="mb-2">
              <button
                onClick={() => setDocsOpen(!docsOpen)}
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-chat-hover transition-colors text-sm"
              >
                <span className="flex items-center gap-2 text-chat-text">
                  <FileText size={16} className="text-chat-accent" />
                  Ver documentos
                </span>
                {docsOpen ? <ChevronDown size={16} className="text-chat-text-secondary" /> : <ChevronRight size={16} className="text-chat-text-secondary" />}
              </button>

              <AnimatePresence>
                {docsOpen && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 p-3 bg-primary-dark/50 border border-chat-border rounded-xl space-y-1 max-h-48 overflow-y-auto"
                  >
                    {stats.fontes.map((fonte, index) => (
                      <div
                        key={index}
                        className="group flex items-center justify-between gap-2 text-xs text-chat-text-secondary py-1.5 px-2 rounded-lg hover:bg-chat-hover transition-colors"
                      >
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <div className="w-1.5 h-1.5 rounded-full bg-chat-accent flex-shrink-0" />
                          <span className="truncate" title={fonte}>{formatSource(fonte)}</span>
                        </div>
                        {onDeleteDocument && (
                          <button
                            onClick={() => handleDeleteDocument(fonte)}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 transition-all"
                            title="Remover documento"
                          >
                            <Trash2 size={12} className="text-red-400" />
                          </button>
                        )}
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* User Section */}
        {user && (
          <div className="p-4 border-t border-chat-border">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full bg-chat-accent/20 flex items-center justify-center">
                <UserIcon size={16} className="text-chat-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-chat-text truncate">{user.username}</p>
                <p className="text-xs text-chat-text-secondary truncate">{user.email}</p>
              </div>
              {onLogout && (
                <button
                  onClick={onLogout}
                  className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                  title="Sair"
                >
                  <LogOut size={16} className="text-red-400" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Bottom Options */}
        <div className="p-4 border-t border-chat-border">
          <div className="mb-2">
            <button
              onClick={() => setOptionsOpen(!optionsOpen)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-chat-hover transition-colors text-sm"
            >
              <span className="flex items-center gap-2 text-chat-text">
                <Settings size={16} className="text-chat-text-secondary" />
                Opcoes
              </span>
              {optionsOpen ? <ChevronDown size={16} className="text-chat-text-secondary" /> : <ChevronRight size={16} className="text-chat-text-secondary" />}
            </button>

            <AnimatePresence>
              {optionsOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 space-y-3"
                >
                  <button
                    onClick={onClear}
                    className="w-full flex items-center gap-2 px-3 py-2.5 text-red-400 hover:bg-red-500/10 rounded-xl transition-colors text-sm"
                  >
                    <Trash2 size={16} />
                    Limpar tudo
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-30"
          onClick={onToggle}
        />
      )}
    </>
  )
}
