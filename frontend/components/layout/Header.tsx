'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';
import { AuthButton } from '../auth/AuthButton';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

export function Header() {
  const { isSidebarOpen, setSidebarOpen } = useAgentStore();
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-4 z-30 mx-4 md:mx-6 flex h-14 items-center justify-between rounded-2xl border border-zinc-200/80 dark:border-white/6 bg-white/80 dark:bg-zinc-950/60 backdrop-blur-2xl px-4 shadow-lg shadow-black/[0.03] dark:shadow-black/20">
      {/* Left: Hamburger + Conditional Brand */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setSidebarOpen(!isSidebarOpen)}
          className="p-2 -ml-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-white/4 text-muted-foreground transition-colors duration-200 focus-ring outline-none"
          aria-label="Toggle Sidebar"
        >
          <Icons.Menu className="h-5 w-5" />
        </button>

        <AnimatePresence mode="wait">
          {!isSidebarOpen ? (
            <motion.div
              key="brand-full"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-2.5"
            >
              <Link href="/" className="flex items-center gap-2.5 group outline-none focus-ring rounded-lg">
                <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 dark:bg-[#1E1E1E] border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden group-hover:border-primary/50 transition-colors">
                  <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} priority className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
                </div>
                <span className="font-display text-[15px] font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
                  Anurag&apos;s Cortex
                </span>
              </Link>
              {/* Online status dot */}
              <div className="relative flex h-2 w-2 items-center justify-center ml-1">
                <div className="h-1.5 w-1.5 rounded-full bg-success" />
                <div className="absolute h-3 w-3 rounded-full bg-success animate-ping opacity-20" />
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="brand-dot"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.15 }}
              className="flex items-center"
            >
              {/* Just a green online dot when sidebar is open */}
              <div className="relative flex h-2 w-2 items-center justify-center ml-1">
                <div className="h-1.5 w-1.5 rounded-full bg-success" />
                <div className="absolute h-3 w-3 rounded-full bg-success animate-ping opacity-20" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right: Theme toggle + Auth */}
      <div className="flex items-center gap-1.5">
        <button
          onClick={toggleTheme}
          className="flex h-8 w-8 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-zinc-100 dark:hover:bg-white/6 transition-all outline-none focus-ring"
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
        <div className="w-px h-5 bg-zinc-200 dark:bg-white/8 mx-1" />
        <AuthButton className="text-sm" />
      </div>
    </header>
  );
}
