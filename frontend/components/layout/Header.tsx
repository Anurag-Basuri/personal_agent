'use client';

import { motion } from 'framer-motion';
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
    <header className="sticky top-4 z-30 mx-4 md:mx-6 flex h-14 items-center justify-between rounded-2xl border border-zinc-200/80 dark:border-white/6 bg-white/80 dark:bg-zinc-950/60 backdrop-blur-2xl px-4 shadow-lg">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(!isSidebarOpen)}
          className="p-2 -ml-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-white/4 text-muted-foreground transition-colors duration-200 focus-ring outline-none"
          aria-label="Toggle Sidebar"
        >
          <Icons.Menu className="h-5 w-5" />
        </button>
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <Link href="/" className="flex items-center gap-2.5 group outline-none focus-ring rounded-lg">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-[#1E1E1E] border border-zinc-800 shadow-sm overflow-hidden group-hover:border-primary/50 transition-colors">
              <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} priority className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
            </div>
            <span className="font-display text-[15px] font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
              Anurag's Cortex
            </span>
          </Link>

          <span className="text-zinc-300 dark:text-zinc-800 hidden sm:block">/</span>
          <span className="text-xs font-semibold text-muted-foreground hidden sm:block font-mono tracking-wide">
            Active Session
          </span>

          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-zinc-100/80 dark:bg-white/3 border border-zinc-200/50 dark:border-white/4 ml-2">
            <div className="relative flex h-2 w-2 items-center justify-center">
              <div className="h-1.5 w-1.5 rounded-full bg-success" />
              <div className="absolute h-3 w-3 rounded-full bg-success animate-ping opacity-20" />
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-[10px] font-bold text-success uppercase tracking-wider font-mono">
                Sys_Ops
              </span>
              <span className="text-[9px] text-muted-foreground/60 font-mono font-medium">
                12ms
              </span>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 bg-zinc-100/80 dark:bg-white/3 p-1 rounded-xl border border-zinc-200/50 dark:border-white/4">
          <Link
            href="/"
            className="hidden sm:flex h-7 px-2.5 items-center justify-center rounded-lg text-xs font-semibold text-muted-foreground hover:text-foreground transition-all hover:bg-white dark:hover:bg-white/10 shadow-sm outline-none focus-ring"
          >
            <Icons.Home className="h-3.5 w-3.5 mr-1.5" />
            Home
          </Link>
          <button
            onClick={toggleTheme}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground transition-all hover:bg-white dark:hover:bg-white/10 shadow-sm outline-none focus-ring"
            aria-label="Toggle theme"
          >
            {resolvedTheme === 'dark' ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
          </button>
        </div>
        <AuthButton className="h-9 px-4 text-xs font-semibold rounded-xl shadow-sm" />
      </div>
    </header>
  );
}
