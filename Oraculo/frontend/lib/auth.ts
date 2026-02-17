/**
 * Auth utilities for the Oraculo frontend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface User {
  id: number
  email: string
  username: string
  created_at: string
  is_active: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// Token management
const TOKEN_KEY = 'oraculo_token'
const USER_KEY = 'oraculo_user'

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(TOKEN_KEY)
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  const userStr = localStorage.getItem(USER_KEY)
  if (!userStr) return null
  try {
    return JSON.parse(userStr)
  } catch {
    return null
  }
}

export function setStoredUser(user: User): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeStoredUser(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(USER_KEY)
}

// API functions
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao fazer login')
  }

  const data: AuthResponse = await response.json()

  // Save token and user
  setToken(data.access_token)
  setStoredUser(data.user)

  return data
}

export async function register(data: RegisterData): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao criar conta')
  }

  const authData: AuthResponse = await response.json()

  // Save token and user
  setToken(authData.access_token)
  setStoredUser(authData.user)

  return authData
}

export async function getCurrentUser(): Promise<User | null> {
  const token = getToken()
  if (!token) return null

  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      // Token invalid or expired
      removeToken()
      removeStoredUser()
      return null
    }

    const user: User = await response.json()
    setStoredUser(user)
    return user
  } catch {
    return null
  }
}

export function logout(): void {
  removeToken()
  removeStoredUser()
}

// Helper to get auth headers
export function getAuthHeaders(): HeadersInit {
  const token = getToken()
  if (!token) return {}
  return {
    'Authorization': `Bearer ${token}`,
  }
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  return !!getToken()
}
