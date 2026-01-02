"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

export function ModeToggle() {
  const { setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => setMounted(true), [])

  if (!mounted) {
    return <div className="w-16 h-9 rounded-full bg-muted/20 animate-pulse" />
  }

  const isDark = resolvedTheme === "dark"

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="group relative flex h-9 w-[64px] items-center rounded-full bg-zinc-200/50 dark:bg-zinc-800/50 p-1 transition-all duration-500 border border-white/10 shadow-inner overflow-hidden"
      aria-label="Toggle theme"
    >
      <div
        className={`flex h-7 w-7 items-center justify-center rounded-full bg-white dark:bg-zinc-950 shadow-[0_2px_10px_rgba(0,0,0,0.2)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.5)] transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] z-10 ${isDark ? "translate-x-7" : "translate-x-0"
          }`}
      >
        {isDark ? (
          <Moon className="h-4 w-4 text-blue-400 fill-blue-400/20 transition-transform group-hover:-rotate-12" />
        ) : (
          <Sun className="h-4 w-4 text-orange-500 fill-orange-500/20 transition-transform group-hover:rotate-12" />
        )}
      </div>

      <div className="absolute inset-0 flex items-center justify-between px-2.5 opacity-30 group-hover:opacity-60 transition-opacity">
        <Sun size={12} className={isDark ? "visible" : "invisible"} />
        <Moon size={12} className={isDark ? "invisible" : "visible"} />
      </div>
    </button>
  )
}
