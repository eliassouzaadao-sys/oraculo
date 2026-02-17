/**
 * Utilitarios de exportacao de conversas.
 */
import { Conversation, Message } from './storage'

/**
 * Formata uma data para exibicao.
 */
function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

/**
 * Exporta conversa como texto simples.
 */
export function exportAsText(conversation: Conversation): string {
  const lines: string[] = [
    `Conversa: ${conversation.title}`,
    `Data: ${formatDate(conversation.createdAt)}`,
    '',
    '---',
    '',
  ]

  for (const message of conversation.messages) {
    const role = message.role === 'user' ? 'Voce' : 'Oraculo'
    lines.push(`${role}:`)
    lines.push(message.content)

    if (message.sources && message.sources.length > 0) {
      lines.push('')
      lines.push('Fontes:')
      for (const source of message.sources) {
        lines.push(`  - ${source.name}`)
      }
    }

    lines.push('')
    lines.push('---')
    lines.push('')
  }

  return lines.join('\n')
}

/**
 * Exporta conversa como Markdown.
 */
export function exportAsMarkdown(conversation: Conversation): string {
  const lines: string[] = [
    `# ${conversation.title}`,
    '',
    `> Exportado em ${formatDate(Date.now())}`,
    '',
    '---',
    '',
  ]

  for (const message of conversation.messages) {
    if (message.role === 'user') {
      lines.push('## Voce')
    } else {
      lines.push('## Oraculo')
    }

    lines.push('')
    lines.push(message.content)
    lines.push('')

    if (message.sources && message.sources.length > 0) {
      lines.push('**Fontes consultadas:**')
      for (const source of message.sources) {
        const score = source.score ? ` (${Math.round(source.score * 100)}%)` : ''
        lines.push(`- ${source.name}${score}`)
      }
      lines.push('')
    }

    lines.push('---')
    lines.push('')
  }

  return lines.join('\n')
}

/**
 * Exporta conversa como JSON.
 */
export function exportAsJson(conversation: Conversation): string {
  return JSON.stringify(conversation, null, 2)
}

/**
 * Dispara download de arquivo.
 */
export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * Exporta e faz download da conversa.
 */
export function downloadConversation(
  conversation: Conversation,
  format: 'txt' | 'md' | 'json' = 'md'
): void {
  const sanitizedTitle = conversation.title
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .slice(0, 30)

  const timestamp = new Date().toISOString().split('T')[0]
  const baseFilename = `oraculo_${sanitizedTitle}_${timestamp}`

  let content: string
  let filename: string
  let mimeType: string

  switch (format) {
    case 'txt':
      content = exportAsText(conversation)
      filename = `${baseFilename}.txt`
      mimeType = 'text/plain'
      break
    case 'json':
      content = exportAsJson(conversation)
      filename = `${baseFilename}.json`
      mimeType = 'application/json'
      break
    case 'md':
    default:
      content = exportAsMarkdown(conversation)
      filename = `${baseFilename}.md`
      mimeType = 'text/markdown'
      break
  }

  downloadFile(content, filename, mimeType)
}

/**
 * Exporta todas as conversas como JSON.
 */
export function downloadAllConversations(conversations: Conversation[]): void {
  const timestamp = new Date().toISOString().split('T')[0]
  const content = JSON.stringify(conversations, null, 2)
  downloadFile(content, `oraculo_backup_${timestamp}.json`, 'application/json')
}
