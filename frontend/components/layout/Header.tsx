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
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-zinc-200 dark:border-white/6 bg-white/80 dark:bg-zinc-950/40 backdrop-blur-2xl px-4 md:px-6">
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
              <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
            </div>
            <span className="font-display text-[15px] font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
              Anurag's Cortex
            </span>
          </Link>
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-muted border border-zinc-200 dark:border-border">
            <div className="relative">
              <div className="h-1.5 w-1.5 rounded-full bg-success" />
              <div className="absolute inset-0 h-1.5 w-1.5 rounded-full bg-success animate-ping opacity-25" />
            </div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              Connected
            </span>
          </div>
        </motion.div>
      </div>

      <div className="flex items-center gap-2">
        <Link
          href="/"
          className="hidden sm:flex h-8 items-center gap-1.5 px-3 rounded-lg text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-zinc-100 dark:hover:bg-muted transition-colors focus-ring outline-none"
        >
          <Icons.Home className="h-3.5 w-3.5" />
          Home
        </Link>
        <button
          onClick={toggleTheme}
          className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-zinc-100 dark:hover:bg-muted text-muted-foreground transition-colors focus-ring outline-none"
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
        <AuthButton className="h-8 px-3 text-xs" />
      </div>
    </header>
  );
}
