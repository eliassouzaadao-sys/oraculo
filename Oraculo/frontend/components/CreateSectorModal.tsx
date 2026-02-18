'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Building2, Palette, Check } from 'lucide-react'
import { useSector } from '@/context/SectorContext'
import toast from 'react-hot-toast'

interface CreateSectorModalProps {
  isOpen: boolean
  onClose: () => void
}

const PRESET_COLORS = [
  '#6366f1', // Indigo
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#ef4444', // Red
  '#f97316', // Orange
  '#eab308', // Yellow
  '#22c55e', // Green
  '#14b8a6', // Teal
  '#0ea5e9', // Sky
  '#3b82f6', // Blue
]

export default function CreateSectorModal({ isOpen, onClose }: CreateSectorModalProps) {
  const { createSector } = useSector()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState(PRESET_COLORS[0])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      toast.error('Digite o nome do setor')
      return
    }

    setLoading(true)

    try {
      await createSector({
        name: name.trim(),
        description: description.trim() || undefined,
        color,
        icon: 'building-2'
      })

      toast.success('Setor criado com sucesso!')
      onClose()
      setName('')
      setDescription('')
      setColor(PRESET_COLORS[0])
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar setor')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      onClose()
      setName('')
      setDescription('')
      setColor(PRESET_COLORS[0])
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md mx-4 bg-chat-sidebar border border-chat-border rounded-2xl shadow-xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-chat-border">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: color + '20' }}
                >
                  <Building2 size={20} style={{ color }} />
                </div>
                <h2 className="text-lg font-semibold text-chat-text">Novo Setor</h2>
              </div>
              <button
                onClick={handleClose}
                disabled={loading}
                className="p-2 rounded-lg hover:bg-chat-hover transition-colors text-chat-text-secondary"
              >
                <X size={20} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-chat-text mb-2">
                  Nome do Setor *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Recursos Humanos, TI, Marketing..."
                  className="w-full px-4 py-3 bg-chat-input border border-chat-border rounded-xl text-chat-text placeholder:text-chat-text-secondary focus:outline-none focus:ring-2 focus:ring-chat-accent/50 focus:border-chat-accent"
                  disabled={loading}
                  autoFocus
                />
              </div>

              {/* Descricao */}
              <div>
                <label className="block text-sm font-medium text-chat-text mb-2">
                  Descricao (opcional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Descreva o proposito deste setor..."
                  rows={3}
                  className="w-full px-4 py-3 bg-chat-input border border-chat-border rounded-xl text-chat-text placeholder:text-chat-text-secondary focus:outline-none focus:ring-2 focus:ring-chat-accent/50 focus:border-chat-accent resize-none"
                  disabled={loading}
                />
              </div>

              {/* Cor */}
              <div>
                <label className="block text-sm font-medium text-chat-text mb-2 flex items-center gap-2">
                  <Palette size={16} />
                  Cor do Setor
                </label>
                <div className="flex flex-wrap gap-2">
                  {PRESET_COLORS.map((presetColor) => (
                    <button
                      key={presetColor}
                      type="button"
                      onClick={() => setColor(presetColor)}
                      className={`
                        w-8 h-8 rounded-lg flex items-center justify-center transition-all
                        ${color === presetColor ? 'ring-2 ring-white ring-offset-2 ring-offset-chat-sidebar' : 'hover:scale-110'}
                      `}
                      style={{ backgroundColor: presetColor }}
                      disabled={loading}
                    >
                      {color === presetColor && <Check size={16} className="text-white" />}
                    </button>
                  ))}
                </div>
              </div>

              {/* Preview */}
              <div className="p-4 bg-chat-hover rounded-xl">
                <p className="text-xs text-chat-text-secondary mb-2">Preview:</p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: color + '20' }}
                  >
                    <Building2 size={18} style={{ color }} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-chat-text">
                      {name || 'Nome do Setor'}
                    </p>
                    <p className="text-xs text-chat-text-secondary">
                      {description || 'Descricao do setor'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Botoes */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={loading}
                  className="flex-1 px-4 py-3 bg-chat-hover text-chat-text rounded-xl hover:bg-chat-input transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading || !name.trim()}
                  className="flex-1 px-4 py-3 bg-chat-accent text-white rounded-xl hover:bg-chat-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? 'Criando...' : 'Criar Setor'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
