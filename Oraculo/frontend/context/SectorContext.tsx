'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getToken } from '@/lib/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Sector {
  id: number
  name: string
  slug: string
  description?: string
  color: string
  icon: string
  created_at: string
  is_active: boolean
  member_count: number
  document_count: number
}

interface CreateSectorData {
  name: string
  description?: string
  color?: string
  icon?: string
}

interface UpdateSectorData {
  name?: string
  description?: string
  color?: string
  icon?: string
  is_active?: boolean
}

interface SectorContextType {
  sectors: Sector[]
  activeSector: Sector | null
  loading: boolean
  error: string | null
  setActiveSector: (sector: Sector) => void
  refreshSectors: () => Promise<void>
  createSector: (data: CreateSectorData) => Promise<Sector>
  updateSector: (id: number, data: UpdateSectorData) => Promise<Sector>
  deleteSector: (id: number) => Promise<void>
  joinSector: (id: number) => Promise<void>
}

const SectorContext = createContext<SectorContextType | undefined>(undefined)

const STORAGE_KEY = 'oraculo_active_sector'

export function SectorProvider({ children }: { children: React.ReactNode }) {
  const [sectors, setSectors] = useState<Sector[]>([])
  const [activeSector, setActiveSectorState] = useState<Sector | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = useCallback(() => {
    const token = getToken()
    return token
      ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      : { 'Content-Type': 'application/json' }
  }, [])

  const refreshSectors = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const token = getToken()
      if (!token) {
        setSectors([])
        setActiveSectorState(null)
        return
      }

      const res = await fetch(`${API_URL}/sectors`, {
        headers: getAuthHeaders()
      })

      if (res.ok) {
        const data: Sector[] = await res.json()
        setSectors(data)

        // Se nao tem setor ativo, tenta recuperar do localStorage ou usa o primeiro
        if (data.length > 0) {
          const savedId = localStorage.getItem(STORAGE_KEY)
          const savedSector = savedId
            ? data.find((s) => s.id.toString() === savedId)
            : null

          if (savedSector) {
            setActiveSectorState(savedSector)
          } else if (!activeSector) {
            setActiveSectorState(data[0])
            localStorage.setItem(STORAGE_KEY, data[0].id.toString())
          }
        } else {
          setActiveSectorState(null)
        }
      } else {
        const err = await res.json()
        setError(err.detail || 'Erro ao carregar setores')
      }
    } catch (err) {
      console.error('Erro ao carregar setores:', err)
      setError('Erro ao carregar setores')
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders, activeSector])

  const setActiveSector = useCallback((sector: Sector) => {
    setActiveSectorState(sector)
    localStorage.setItem(STORAGE_KEY, sector.id.toString())

    // Atualiza no servidor
    const token = getToken()
    if (token) {
      fetch(`${API_URL}/users/me/active-sector?sector_id=${sector.id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(console.error)
    }
  }, [])

  const createSector = useCallback(async (data: CreateSectorData): Promise<Sector> => {
    const res = await fetch(`${API_URL}/sectors`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao criar setor')
    }

    const sector: Sector = await res.json()
    await refreshSectors()

    // Seleciona o novo setor como ativo
    setActiveSector(sector)

    return sector
  }, [getAuthHeaders, refreshSectors, setActiveSector])

  const updateSector = useCallback(async (id: number, data: UpdateSectorData): Promise<Sector> => {
    const res = await fetch(`${API_URL}/sectors/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao atualizar setor')
    }

    const sector: Sector = await res.json()
    await refreshSectors()

    // Se atualizou o setor ativo, atualiza o estado
    if (activeSector?.id === id) {
      setActiveSectorState(sector)
    }

    return sector
  }, [getAuthHeaders, refreshSectors, activeSector])

  const deleteSector = useCallback(async (id: number) => {
    const res = await fetch(`${API_URL}/sectors/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao deletar setor')
    }

    await refreshSectors()

    // Se deletou o setor ativo, seleciona outro
    if (activeSector?.id === id) {
      const remaining = sectors.filter(s => s.id !== id)
      if (remaining.length > 0) {
        setActiveSector(remaining[0])
      } else {
        setActiveSectorState(null)
        localStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [getAuthHeaders, refreshSectors, activeSector, sectors, setActiveSector])

  const joinSector = useCallback(async (id: number) => {
    const res = await fetch(`${API_URL}/sectors/${id}/join`, {
      method: 'POST',
      headers: getAuthHeaders()
    })

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao entrar no setor')
    }

    await refreshSectors()
  }, [getAuthHeaders, refreshSectors])

  // Carrega setores na montagem
  useEffect(() => {
    refreshSectors()
  }, [])

  // Recarrega quando o token muda (login/logout)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'oraculo_token') {
        refreshSectors()
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [refreshSectors])

  const value: SectorContextType = {
    sectors,
    activeSector,
    loading,
    error,
    setActiveSector,
    refreshSectors,
    createSector,
    updateSector,
    deleteSector,
    joinSector,
  }

  return (
    <SectorContext.Provider value={value}>
      {children}
    </SectorContext.Provider>
  )
}

export function useSector() {
  const context = useContext(SectorContext)
  if (context === undefined) {
    throw new Error('useSector must be used within a SectorProvider')
  }
  return context
}
