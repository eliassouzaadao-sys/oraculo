'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { useAuth } from '@/context/AuthContext'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ email, password })
      router.push('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-chat-sidebar flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo Horizontal */}
        <div className="flex flex-col items-center mb-8">
          <Image
            src="/logo-horizontal.png"
            alt="Oraculo"
            width={240}
            height={80}
            className="object-contain"
          />
        </div>

        {/* Card */}
        <div className="bg-chat-bg rounded-xl border border-chat-border p-6">
          <h2 className="text-xl font-bold text-chat-text mb-6 text-center">
            Entrar
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-chat-text mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2 bg-chat-input border border-chat-border rounded-lg text-chat-text placeholder-chat-text-secondary focus:outline-none focus:ring-2 focus:ring-chat-accent focus:border-transparent font-normal"
                placeholder="seu@email.com"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-chat-text mb-1">
                Senha
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 bg-chat-input border border-chat-border rounded-lg text-chat-text placeholder-chat-text-secondary focus:outline-none focus:ring-2 focus:ring-chat-accent focus:border-transparent font-normal"
                placeholder="********"
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <p className="text-sm text-red-400 font-normal">{error}</p>
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 gradient-accent text-white font-semibold rounded-xl transition-all hover:opacity-90 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-chat-accent focus:ring-offset-2 focus:ring-offset-chat-bg shadow-glow-sm hover:shadow-glow"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          {/* Register link */}
          <div className="mt-6 text-center">
            <p className="text-chat-text-secondary font-normal">
              Nao tem uma conta?{' '}
              <Link href="/auth/register" className="text-chat-accent hover:underline font-semibold">
                Criar conta
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
