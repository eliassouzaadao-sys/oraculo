/**
 * Utilitarios de armazenamento local para o Oraculo.
 * Gerencia conversas, preferencias e historico.
 */

// Tipos
export interface Source {
  name: string
  score?: number
  excerpt?: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp?: number
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

// Chaves de storage
const STORAGE_KEYS = {
  CONVERSATIONS: 'oraculo_conversations',
  ACTIVE_CONVERSATION: 'oraculo_active_conversation',
  SETTINGS: 'oraculo_settings',
} as const

// Limite de conversas armazenadas
const MAX_CONVERSATIONS = 50

/**
 * Gera um ID unico para conversas.
 */
export function generateId(): string {
  return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Extrai titulo da conversa a partir das mensagens.
 */
export function extractTitle(messages: Message[]): string {
  const firstUserMessage = messages.find(m => m.role === 'user')
  if (!firstUserMessage) return 'Nova conversa'

  const title = firstUserMessage.content.slice(0, 50)
  return title.length < firstUserMessage.content.length ? `${title}...` : title
}

/**
 * Carrega todas as conversas do localStorage.
 */
export function loadConversations(): Conversation[] {
  if (typeof window === 'undefined') return []

  try {
    const data = localStorage.getItem(STORAGE_KEYS.CONVERSATIONS)
    if (!data) return []

    const conversations = JSON.parse(data) as Conversation[]
    // Ordena por data de atualizacao (mais recente primeiro)
    return conversations.sort((a, b) => b.updatedAt - a.updatedAt)
  } catch (error) {
    console.error('Erro ao carregar conversas:', error)
    return []
  }
}

/**
 * Salva todas as conversas no localStorage.
 */
export function saveConversations(conversations: Conversation[]): void {
  if (typeof window === 'undefined') return

  try {
    // Limita a quantidade de conversas
    const limitedConversations = conversations
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, MAX_CONVERSATIONS)

    localStorage.setItem(STORAGE_KEYS.CONVERSATIONS, JSON.stringify(limitedConversations))
  } catch (error) {
    console.error('Erro ao salvar conversas:', error)
  }
}

/**
 * Carrega uma conversa especifica pelo ID.
 */
export function loadConversation(id: string): Conversation | null {
  const conversations = loadConversations()
  return conversations.find(c => c.id === id) || null
}

/**
 * Salva ou atualiza uma conversa.
 */
export function saveConversation(conversation: Conversation): void {
  const conversations = loadConversations()
  const index = conversations.findIndex(c => c.id === conversation.id)

  if (index >= 0) {
    conversations[index] = conversation
  } else {
    conversations.unshift(conversation)
  }

  saveConversations(conversations)
}

/**
 * Cria uma nova conversa.
 */
export function createConversation(messages: Message[] = []): Conversation {
  const now = Date.now()
  const conversation: Conversation = {
    id: generateId(),
    title: extractTitle(messages),
    messages,
    createdAt: now,
    updatedAt: now,
  }

  saveConversation(conversation)
  setActiveConversationId(conversation.id)

  return conversation
}

/**
 * Atualiza mensagens de uma conversa.
 */
export function updateConversationMessages(id: string, messages: Message[]): void {
  const conversation = loadConversation(id)
  if (!conversation) return

  conversation.messages = messages
  conversation.title = extractTitle(messages)
  conversation.updatedAt = Date.now()

  saveConversation(conversation)
}

/**
 * Deleta uma conversa.
 */
export function deleteConversation(id: string): void {
  const conversations = loadConversations()
  const filtered = conversations.filter(c => c.id !== id)
  saveConversations(filtered)

  // Se era a conversa ativa, limpa
  if (getActiveConversationId() === id) {
    setActiveConversationId(null)
  }
}

/**
 * Obtem o ID da conversa ativa.
 */
export function getActiveConversationId(): string | null {
  if (typeof window === 'undefined') return null

  try {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_CONVERSATION)
  } catch {
    return null
  }
}

/**
 * Define a conversa ativa.
 */
export function setActiveConversationId(id: string | null): void {
  if (typeof window === 'undefined') return

  try {
    if (id) {
      localStorage.setItem(STORAGE_KEYS.ACTIVE_CONVERSATION, id)
    } else {
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_CONVERSATION)
    }
  } catch (error) {
    console.error('Erro ao definir conversa ativa:', error)
  }
}

/**
 * Limpa todas as conversas.
 */
export function clearAllConversations(): void {
  if (typeof window === 'undefined') return

  try {
    localStorage.removeItem(STORAGE_KEYS.CONVERSATIONS)
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_CONVERSATION)
  } catch (error) {
    console.error('Erro ao limpar conversas:', error)
  }
}

// Configuracoes
export interface Settings {
  theme: 'dark' | 'light' | 'system'
}

const DEFAULT_SETTINGS: Settings = {
  theme: 'dark',
}

/**
 * Carrega configuracoes.
 */
export function loadSettings(): Settings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS

  try {
    const data = localStorage.getItem(STORAGE_KEYS.SETTINGS)
    if (!data) return DEFAULT_SETTINGS
    return { ...DEFAULT_SETTINGS, ...JSON.parse(data) }
  } catch {
    return DEFAULT_SETTINGS
  }
}

/**
 * Salva configuracoes.
 */
export function saveSettings(settings: Partial<Settings>): void {
  if (typeof window === 'undefined') return

  try {
    const current = loadSettings()
    const updated = { ...current, ...settings }
    localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(updated))
  } catch (error) {
    console.error('Erro ao salvar configuracoes:', error)
  }
}
