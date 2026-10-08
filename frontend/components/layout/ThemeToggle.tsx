'use client'

import { useState, useEffect, useRef } from 'react'
import { useTheme } from 'next-themes'
import { Sun, Moon, Monitor, Check, ChevronDown } from 'lucide-react'

const THEMES = [
  { id: 'light', label: 'Light', icon: Sun, iconColor: 'text-amber-500' },
  { id: 'dark', label: 'Dark', icon: Moon, iconColor: 'text-indigo-400' },
  { id: 'system', label: 'System', icon: Monitor, iconColor: 'text-sky-400' },
] as const

export default function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="h-8 w-14 rounded-xl bg-[var(--bg)] border border-[var(--border)] animate-pulse" />
    )
  }

  const currentTheme = THEMES.find((t) => t.id === theme) ?? THEMES[2]
  const CurrentIcon = currentTheme.icon

  return (
    <div className="relative inline-block" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={`Toggle theme, current is ${currentTheme.label}`}
        aria-haspopup="true"
        aria-expanded={isOpen}
        title={`Theme: ${currentTheme.label}${theme === 'system' ? ` (${resolvedTheme === 'dark' ? 'Dark' : 'Light'})` : ''}`}
        className="flex items-center gap-1.5 h-8 px-2.5 rounded-xl bg-[var(--bg)] border border-[var(--border)] hover:border-[var(--muted)]/50 text-[var(--text)] transition-all cursor-pointer shadow-sm select-none"
      >
        <CurrentIcon size={14} className={currentTheme.iconColor} />
        <span className="text-xs font-medium hidden sm:inline">{currentTheme.label}</span>
        <ChevronDown
          size={12}
          className={`text-[var(--muted)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 top-full mt-2 w-36 rounded-xl bg-[var(--surface)] border border-[var(--border)] shadow-xl p-1 z-50 backdrop-blur-md transition-all animate-in fade-in zoom-in-95 duration-150"
        >
          {THEMES.map(({ id, label, icon: Icon, iconColor }) => {
            const isSelected = theme === id
            return (
              <button
                key={id}
                role="menuitem"
                onClick={() => {
                  setTheme(id)
                  setIsOpen(false)
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-[var(--blue)]/10 text-[var(--blue)] font-medium'
                    : 'text-[var(--text)] hover:bg-[var(--surface-hover)]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon size={14} className={iconColor} />
                  <span>{label}</span>
                </div>
                {isSelected && <Check size={13} className="text-[var(--blue)]" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
