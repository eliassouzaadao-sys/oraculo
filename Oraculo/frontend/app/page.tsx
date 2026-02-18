'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import Sidebar from '@/components/Sidebar'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import WelcomeScreen from '@/components/WelcomeScreen'
import AuthGuard from '@/components/AuthGuard'
import { useAuth } from '@/context/AuthContext'
import { useSector } from '@/context/SectorContext'
import {
  Message,
  Source,
  Conversation,
  loadConversations,
  loadConversation,
  saveConversation,
  createConversation,
  updateConversationMessages,
  getActiveConversationId,
  setActiveConversationId,
  generateId,
  extractTitle
} from '@/lib/storage'

interface Stats {
  total_documentos: number
  total_chunks: number
  fontes: string[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const { user, logout } = useAuth()
  const { activeSector, refreshSectors } = useSector()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [stats, setStats] = useState<Stats>({ total_documentos: 0, total_chunks: 0, fontes: [] })
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeConversationId, setActiveConvId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Carrega estatisticas do setor
  const loadStats = useCallback(async () => {
    try {
      const sectorParam = activeSector ? `?sector_id=${activeSector.id}` : ''
      const res = await fetch(`${API_URL}/stats${sectorParam}`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Erro ao carregar stats:', error)
    }
  }, [activeSector])

  // Inicializacao e ao trocar de setor
  useEffect(() => {
    loadStats()

    // Sempre limpa ao trocar de setor
    setActiveConvId(null)
    setMessages([])
    setActiveConversationId(null)

    // So tenta carregar conversa se tiver setor ativo
    if (activeSector) {
      const savedId = getActiveConversationId()
      if (savedId) {
        const conversation = loadConversation(savedId)
        // Verifica se conversa pertence ao setor atual
        if (conversation && conversation.sectorId === activeSector.id.toString()) {
          setActiveConvId(savedId)
          setMessages(conversation.messages)
        }
      }
    }
  }, [loadStats, activeSector])

  // Scroll para o fim
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Salva mensagens no localStorage quando mudam
  useEffect(() => {
    if (activeConversationId && messages.length > 0) {
      updateConversationMessages(activeConversationId, messages)
    }
  }, [messages, activeConversationId])

  // Envia mensagem
  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    // Verifica se tem setor ativo
    if (!activeSector) {
      toast.error('Selecione um setor primeiro')
      return
    }

    // Se nao ha conversa ativa, cria uma nova vinculada ao setor
    let currentConvId = activeConversationId
    if (!currentConvId) {
      const newConv = createConversation([], activeSector.id.toString())
      currentConvId = newConv.id
      setActiveConvId(currentConvId)
    }

    // Adiciona mensagem do usuario
    const userMessage: Message = { role: 'user', content, timestamp: Date.now() }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    // Adiciona placeholder para resposta
    setMessages(prev => [...prev, { role: 'assistant', content: '', timestamp: Date.now() }])

    try {
      const res = await fetch(`${API_URL}/chat?sector_id=${activeSector.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content })
      })

      if (!res.ok) {
        throw new Error('Erro na requisicao')
      }

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let sources: Source[] = []

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break

            // Verifica se e um JSON com fontes
            if (data.startsWith('[SOURCES]')) {
              try {
                const sourcesJson = data.replace('[SOURCES]', '')
                sources = JSON.parse(sourcesJson)
              } catch {
                // Ignora erro de parse
              }
            } else {
              // Decodifica newlines que foram codificadas no backend
              const decodedData = data.replace(/\\n/g, '\n')
              fullResponse += decodedData
              setMessages(prev => {
                const newMessages = [...prev]
                newMessages[newMessages.length - 1] = {
                  ...newMessages[newMessages.length - 1],
                  content: fullResponse,
                  sources: sources.length > 0 ? sources : undefined
                }
                return newMessages
              })
            }
          }
        }
      }

      // Atualiza com as fontes finais
      if (sources.length > 0) {
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            ...newMessages[newMessages.length - 1],
            sources
          }
          return newMessages
        })
      }
    } catch (error) {
      toast.error('Erro ao enviar mensagem. Verifique sua conexao.')
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1].content = 'Desculpe, ocorreu um erro. Tente novamente.'
        return newMessages
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Nova conversa
  const newChat = async () => {
    if (!activeSector) {
      toast.error('Selecione um setor primeiro')
      return
    }

    // Limpa memoria no servidor
    try {
      await fetch(`${API_URL}/clear-chat?sector_id=${activeSector.id}`, { method: 'POST' })
    } catch (error) {
      console.error('Erro ao limpar chat:', error)
    }

    // Cria nova conversa no localStorage vinculada ao setor
    const newConv = createConversation([], activeSector.id.toString())
    setActiveConvId(newConv.id)
    setMessages([])
    toast.success('Nova conversa iniciada')
  }

  // Seleciona conversa do historico
  const selectConversation = async (conversation: Conversation) => {
    // Limpa memoria do servidor para a nova conversa
    const sectorParam = activeSector ? `?sector_id=${activeSector.id}` : ''
    try {
      await fetch(`${API_URL}/clear-chat${sectorParam}`, { method: 'POST' })
    } catch (error) {
      console.error('Erro ao limpar chat:', error)
    }

    setActiveConvId(conversation.id)
    setActiveConversationId(conversation.id)
    setMessages(conversation.messages)
  }

  // Upload de arquivo
  const uploadFile = async (file: File) => {
    if (!activeSector) {
      toast.error('Selecione um setor primeiro')
      return false
    }

    const formData = new FormData()
    formData.append('file', file)

    const loadingToast = toast.loading(`Processando ${file.name}...`)

    try {
      const res = await fetch(`${API_URL}/upload?sector_id=${activeSector.id}`, {
        method: 'POST',
        body: formData
      })

      if (res.ok) {
        toast.dismiss(loadingToast)
        toast.success(`${file.name} adicionado com sucesso!`)
        loadStats()
        refreshSectors() // Atualiza contagem de documentos
        return true
      }
      toast.dismiss(loadingToast)
      toast.error(`Erro ao processar ${file.name}`)
      return false
    } catch (error) {
      toast.dismiss(loadingToast)
      toast.error('Erro de conexao ao fazer upload')
      console.error('Erro ao fazer upload:', error)
      return false
    }
  }

  // Adiciona URL
  const addUrl = async (url: string) => {
    if (!activeSector) {
      toast.error('Selecione um setor primeiro')
      return false
    }

    const loadingToast = toast.loading('Processando URL...')

    try {
      const res = await fetch(`${API_URL}/add-url?sector_id=${activeSector.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      })

      toast.dismiss(loadingToast)

      if (res.ok) {
        toast.success('URL adicionada com sucesso!')
        loadStats()
        refreshSectors() // Atualiza contagem de documentos
        return true
      }

      const errorData = await res.json().catch(() => ({ detail: 'Erro ao processar URL' }))
      toast.error(errorData.detail || 'Erro ao processar URL')
      return false
    } catch (error) {
      toast.dismiss(loadingToast)
      toast.error('Erro de conexao')
      console.error('Erro ao adicionar URL:', error)
      return false
    }
  }

  // Deleta documento individual
  const deleteDocument = async (source: string) => {
    const sectorParam = activeSector ? `?sector_id=${activeSector.id}` : ''

    try {
      const res = await fetch(`${API_URL}/documents/${encodeURIComponent(source)}${sectorParam}`, {
        method: 'DELETE'
      })

      if (res.ok) {
        loadStats()
        refreshSectors() // Atualiza contagem de documentos
        return true
      }
      toast.error('Erro ao remover documento')
      return false
    } catch (error) {
      toast.error('Erro de conexao')
      console.error('Erro ao deletar documento:', error)
      return false
    }
  }

  // Limpa base do setor
  const clearDatabase = async () => {
    if (!activeSector) {
      toast.error('Selecione um setor primeiro')
      return
    }

    try {
      await fetch(`${API_URL}/clear?sector_id=${activeSector.id}`, { method: 'POST' })
      setMessages([])
      setActiveConvId(null)
      setActiveConversationId(null)
      loadStats()
      refreshSectors() // Atualiza contagem de documentos
      toast.success('Base de conhecimento do setor limpa')
    } catch (error) {
      toast.error('Erro ao limpar base')
      console.error('Erro ao limpar base:', error)
    }
  }

  return (
    <AuthGuard>
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onNewChat={newChat}
          onUpload={uploadFile}
          onAddUrl={addUrl}
          onClear={clearDatabase}
          onDeleteDocument={deleteDocument}
          onSelectConversation={selectConversation}
          activeConversationId={activeConversationId}
          stats={stats}
          user={user}
          onLogout={logout}
        />

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col bg-chat-bg">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <WelcomeScreen
                stats={stats}
                onSuggestionClick={sendMessage}
              />
            ) : (
              <div className="max-w-chat mx-auto py-8 px-4">
                {messages.map((message, index) => (
                  <ChatMessage
                    key={index}
                    role={message.role}
                    content={message.content}
                    sources={message.sources}
                    isLoading={isLoading && index === messages.length - 1 && message.role === 'assistant'}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 pb-6 bg-gradient-to-t from-chat-bg via-chat-bg to-transparent">
            <ChatInput
              onSend={sendMessage}
              disabled={isLoading || stats.total_documentos === 0}
              placeholder={
                stats.total_documentos === 0
                  ? "Adicione documentos no menu lateral para comecar..."
                  : "Envie uma mensagem..."
              }
            />
            <p className="text-center text-chat-text-secondary text-xs mt-3">
              Oraculo pode cometer erros. Verifique informacoes importantes.
            </p>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
