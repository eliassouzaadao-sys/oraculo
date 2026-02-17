'use client'

import { motion, Variants } from 'framer-motion'
import Image from 'next/image'
import { Lightbulb, FileText, Search, HelpCircle, Upload } from 'lucide-react'

interface Stats {
  total_documentos: number
  total_chunks: number
  fontes: string[]
}

interface WelcomeScreenProps {
  stats: Stats
  onSuggestionClick: (message: string) => void
}

const suggestions = [
  {
    icon: Lightbulb,
    title: 'O que voce sabe?',
    description: 'Resuma o conteudo dos documentos'
  },
  {
    icon: FileText,
    title: 'Faca um resumo',
    description: 'Liste os pontos principais'
  },
  {
    icon: Search,
    title: 'Detalhes importantes',
    description: 'Quais informacoes relevantes tem?'
  },
  {
    icon: HelpCircle,
    title: 'Posso perguntar sobre...',
    description: 'Quais topicos voce conhece?'
  }
]

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    }
  }
}

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4 }
  }
}

const logoVariants: Variants = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.5,
    }
  }
}

export default function WelcomeScreen({ stats, onSuggestionClick }: WelcomeScreenProps) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col items-center justify-center min-h-full p-8"
    >
      {/* Logo Horizontal */}
      <motion.div
        variants={logoVariants}
        className="mb-8"
      >
        <Image
          src="/logo-horizontal.png"
          alt="Oraculo"
          width={240}
          height={80}
          className="object-contain"
        />
      </motion.div>

      {/* Subtitle */}
      <motion.p
        variants={itemVariants}
        className="text-chat-text-secondary text-center mb-10 max-w-md"
      >
        {stats.total_documentos > 0
          ? <>Base com <span className="text-chat-accent font-semibold">{stats.total_documentos}</span> documento(s) - Pergunte qualquer coisa</>
          : 'Adicione documentos no menu lateral para comecar'
        }
      </motion.p>

      {/* Suggestions */}
      {stats.total_documentos > 0 && (
        <motion.div
          variants={containerVariants}
          className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full"
        >
          {suggestions.map((suggestion, index) => (
            <motion.button
              key={index}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSuggestionClick(suggestion.title)}
              className="flex items-start gap-4 p-5 bg-chat-input/50 border border-chat-border rounded-xl hover:bg-chat-hover hover:border-chat-accent/50 transition-colors text-left group hover:shadow-glow-sm"
            >
              <div className="w-10 h-10 rounded-lg bg-chat-accent/20 flex items-center justify-center group-hover:bg-chat-accent/30 transition-colors">
                <suggestion.icon
                  size={20}
                  className="text-chat-accent"
                />
              </div>
              <div className="flex-1">
                <p className="font-medium text-chat-text mb-1">
                  {suggestion.title}
                </p>
                <p className="text-sm text-chat-text-secondary">
                  {suggestion.description}
                </p>
              </div>
            </motion.button>
          ))}
        </motion.div>
      )}

      {/* Empty state */}
      {stats.total_documentos === 0 && (
        <motion.div
          variants={itemVariants}
          className="text-center p-8 border-2 border-dashed border-chat-border rounded-2xl max-w-md"
        >
          <motion.div
            animate={{
              y: [0, -5, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <Upload size={48} className="text-chat-accent mx-auto mb-4" />
          </motion.div>
          <p className="text-chat-text font-medium mb-2">Nenhum documento ainda</p>
          <p className="text-chat-text-secondary text-sm">
            Use o menu lateral para fazer upload de arquivos ou adicionar links
          </p>
        </motion.div>
      )}
    </motion.div>
  )
}
