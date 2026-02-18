'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Plus, Settings, Building2, FileText } from 'lucide-react'
import { useSector, Sector } from '@/context/SectorContext'

interface SectorSelectorProps {
  onCreateClick?: () => void
  onManageClick?: () => void
}

export default function SectorSelector({ onCreateClick, onManageClick }: SectorSelectorProps) {
  const { sectors, activeSector, setActiveSector, loading } = useSector()
  const [isOpen, setIsOpen] = useState(false)

  if (loading) {
    return (
      <div className="w-full h-14 rounded-xl bg-chat-hover animate-pulse" />
    )
  }

  if (sectors.length === 0) {
    return (
      <button
        onClick={onCreateClick}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 border-dashed border-chat-accent/30 hover:border-chat-accent/50 hover:bg-chat-accent/10 transition-colors"
      >
        <Plus size={18} className="text-chat-accent" />
        <span className="text-sm text-chat-text">Criar primeiro setor</span>
      </button>
    )
  }

  if (!activeSector) {
    return (
      <button
        onClick={() => sectors.length > 0 && setActiveSector(sectors[0])}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-chat-hover hover:bg-chat-input transition-colors"
      >
        <Building2 size={18} className="text-chat-text-secondary" />
        <span className="text-sm text-chat-text">Selecionar setor</span>
      </button>
    )
  }

  return (
    <div className="relative">
      {/* Botao do setor ativo */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-chat-hover hover:bg-chat-input transition-colors"
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: activeSector.color + '20' }}
        >
          <Building2 size={16} style={{ color: activeSector.color }} />
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm font-medium text-chat-text truncate">
            {activeSector.name}
          </p>
          <p className="text-xs text-chat-text-secondary flex items-center gap-1">
            <FileText size={10} />
            {activeSector.document_count} documento(s)
          </p>
        </div>
        <ChevronDown
          size={16}
          className={`text-chat-text-secondary transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown de setores */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay para fechar */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 bg-chat-input border border-chat-border rounded-xl shadow-lg z-50 overflow-hidden"
            >
              <div className="max-h-64 overflow-y-auto py-2">
                {sectors.map((sector) => (
                  <button
                    key={sector.id}
                    onClick={() => {
                      setActiveSector(sector)
                      setIsOpen(false)
                    }}
                    className={`
                      w-full flex items-center gap-3 px-4 py-2.5 hover:bg-chat-hover transition-colors
                      ${activeSector.id === sector.id ? 'bg-chat-accent/10' : ''}
                    `}
                  >
                    <div
                      className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: sector.color + '20' }}
                    >
                      <Building2 size={14} style={{ color: sector.color }} />
                    </div>
                    <span className="flex-1 text-left text-sm text-chat-text truncate">
                      {sector.name}
                    </span>
                    <span className="text-xs text-chat-text-secondary flex-shrink-0">
                      {sector.document_count}
                    </span>
                  </button>
                ))}
              </div>

              {/* Acoes */}
              <div className="border-t border-chat-border p-2 space-y-1">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    onCreateClick?.()
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-chat-accent hover:bg-chat-hover rounded-lg transition-colors"
                >
                  <Plus size={14} />
                  Novo setor
                </button>
                {onManageClick && (
                  <button
                    onClick={() => {
                      setIsOpen(false)
                      onManageClick?.()
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-chat-text-secondary hover:bg-chat-hover rounded-lg transition-colors"
                  >
                    <Settings size={14} />
                    Gerenciar setores
                  </button>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
