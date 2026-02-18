'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Building2,
  Plus,
  ArrowLeft,
  FileText,
  Users,
  Trash2,
  Edit2,
  Check,
  X
} from 'lucide-react'
import Link from 'next/link'
import Image from 'next/image'
import toast from 'react-hot-toast'
import { useSector, Sector } from '@/context/SectorContext'
import { useAuth } from '@/context/AuthContext'
import AuthGuard from '@/components/AuthGuard'
import CreateSectorModal from '@/components/CreateSectorModal'

export default function AdminPage() {
  const { user } = useAuth()
  const { sectors, deleteSector, updateSector, refreshSectors, loading } = useSector()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingSector, setEditingSector] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  const handleStartEdit = (sector: Sector) => {
    setEditingSector(sector.id)
    setEditName(sector.name)
    setEditDescription(sector.description || '')
  }

  const handleCancelEdit = () => {
    setEditingSector(null)
    setEditName('')
    setEditDescription('')
  }

  const handleSaveEdit = async (sectorId: number) => {
    try {
      await updateSector(sectorId, {
        name: editName,
        description: editDescription || undefined
      })
      toast.success('Setor atualizado')
      handleCancelEdit()
    } catch (err: any) {
      toast.error(err.message || 'Erro ao atualizar setor')
    }
  }

  const handleDelete = async (sector: Sector) => {
    if (!confirm(`Tem certeza que deseja remover o setor "${sector.name}"? Todos os documentos serao perdidos.`)) {
      return
    }

    try {
      await deleteSector(sector.id)
      toast.success('Setor removido')
    } catch (err: any) {
      toast.error(err.message || 'Erro ao remover setor')
    }
  }

  return (
    <AuthGuard>
      <div className="min-h-screen bg-chat-bg">
        {/* Header */}
        <header className="bg-chat-sidebar border-b border-chat-border">
          <div className="max-w-6xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link
                  href="/"
                  className="p-2 rounded-lg hover:bg-chat-hover transition-colors text-chat-text-secondary"
                >
                  <ArrowLeft size={20} />
                </Link>
                <div className="flex items-center gap-3">
                  <Image
                    src="/logo-symbol.png"
                    alt="Oraculo"
                    width={32}
                    height={32}
                    className="w-8 h-8 object-contain"
                  />
                  <div>
                    <h1 className="text-xl font-bold text-chat-text">Gerenciar Setores</h1>
                    <p className="text-sm text-chat-text-secondary">
                      Administre os setores da sua empresa
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl gradient-accent text-white font-medium hover:opacity-90 transition-all"
              >
                <Plus size={18} />
                Novo Setor
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="max-w-6xl mx-auto px-6 py-8">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-chat-sidebar border border-chat-border rounded-xl p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                  <Building2 size={20} className="text-indigo-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-chat-text">{sectors.length}</p>
                  <p className="text-sm text-chat-text-secondary">Setores</p>
                </div>
              </div>
            </div>

            <div className="bg-chat-sidebar border border-chat-border rounded-xl p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <FileText size={20} className="text-emerald-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-chat-text">
                    {sectors.reduce((acc, s) => acc + s.document_count, 0)}
                  </p>
                  <p className="text-sm text-chat-text-secondary">Documentos Total</p>
                </div>
              </div>
            </div>

            <div className="bg-chat-sidebar border border-chat-border rounded-xl p-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <Users size={20} className="text-amber-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-chat-text">
                    {sectors.reduce((acc, s) => acc + s.member_count, 0)}
                  </p>
                  <p className="text-sm text-chat-text-secondary">Membros Total</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sectors List */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-chat-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : sectors.length === 0 ? (
            <div className="bg-chat-sidebar border border-chat-border rounded-2xl p-12 text-center">
              <Building2 size={48} className="mx-auto text-chat-text-secondary mb-4" />
              <h3 className="text-lg font-semibold text-chat-text mb-2">
                Nenhum setor criado
              </h3>
              <p className="text-chat-text-secondary mb-6">
                Crie seu primeiro setor para comecar a organizar o conhecimento da empresa
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl gradient-accent text-white font-medium hover:opacity-90 transition-all"
              >
                <Plus size={18} />
                Criar Primeiro Setor
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {sectors.map((sector) => (
                <motion.div
                  key={sector.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-chat-sidebar border border-chat-border rounded-xl overflow-hidden"
                >
                  {editingSector === sector.id ? (
                    /* Modo de edicao */
                    <div className="p-5">
                      <div className="flex items-start gap-4">
                        <div
                          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: sector.color + '20' }}
                        >
                          <Building2 size={24} style={{ color: sector.color }} />
                        </div>

                        <div className="flex-1 space-y-3">
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full px-4 py-2 bg-chat-input border border-chat-border rounded-lg text-chat-text focus:outline-none focus:ring-2 focus:ring-chat-accent/50"
                            placeholder="Nome do setor"
                            autoFocus
                          />
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full px-4 py-2 bg-chat-input border border-chat-border rounded-lg text-chat-text focus:outline-none focus:ring-2 focus:ring-chat-accent/50 resize-none"
                            placeholder="Descricao (opcional)"
                            rows={2}
                          />
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleSaveEdit(sector.id)}
                            className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-colors"
                          >
                            <Check size={18} />
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="p-2 rounded-lg bg-chat-hover text-chat-text-secondary hover:bg-chat-input transition-colors"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Modo de visualizacao */
                    <div className="p-5">
                      <div className="flex items-start gap-4">
                        <div
                          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: sector.color + '20' }}
                        >
                          <Building2 size={24} style={{ color: sector.color }} />
                        </div>

                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-chat-text">
                            {sector.name}
                          </h3>
                          {sector.description && (
                            <p className="text-sm text-chat-text-secondary mt-1">
                              {sector.description}
                            </p>
                          )}

                          <div className="flex items-center gap-4 mt-3">
                            <span className="text-sm text-chat-text-secondary flex items-center gap-1">
                              <FileText size={14} />
                              {sector.document_count} documento(s)
                            </span>
                            <span className="text-sm text-chat-text-secondary flex items-center gap-1">
                              <Users size={14} />
                              {sector.member_count} membro(s)
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleStartEdit(sector)}
                            className="p-2 rounded-lg hover:bg-chat-hover transition-colors text-chat-text-secondary"
                            title="Editar"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(sector)}
                            className="p-2 rounded-lg hover:bg-red-500/10 transition-colors text-red-400"
                            title="Remover"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </main>

        {/* Create Sector Modal */}
        <CreateSectorModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
        />
      </div>
    </AuthGuard>
  )
}
