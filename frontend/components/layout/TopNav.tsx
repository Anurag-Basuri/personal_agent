'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import Image from 'next/image';
import { Icons } from '../ui/Icons';
import { AuthButton } from '../auth/AuthButton';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon } from 'lucide-react';

export function TopNav() {
  const { data: session } = useSession();
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', damping: 20, stiffness: 100 }}
      className="fixed left-0 right-0 top-0 z-50 flex justify-center pt-6 px-4 md:px-6 pointer-events-none"
    >
      <div className="relative w-full max-w-5xl pointer-events-auto group">
        {/* Animated Glow Border */}
        <div className="absolute -inset-px rounded-[17px] bg-linear-to-r from-primary/40 via-accent/40 to-secondary/40 opacity-50 blur-[2px] transition-opacity duration-1000 group-hover:opacity-80" />
        
        {/* Main Navbar */}
        <div className="relative flex h-14 w-full items-center justify-between gap-6 rounded-2xl px-4 md:px-6 bg-white/90 dark:bg-zinc-950/80 backdrop-blur-2xl border border-zinc-200/50 dark:border-white/5 shadow-xl">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5 outline-none rounded-lg focus-ring">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden hover:border-primary/50 transition-colors">
              <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} priority className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
            </div>
            <span className="font-display text-[15px] font-bold tracking-tight text-foreground hidden sm:block hover:text-primary transition-colors">
              Anurag's Cortex
            </span>
          </Link>

          {/* Actions */}
          <div className="flex items-center gap-2 md:gap-4">
            <div className="flex items-center gap-1 bg-zinc-100/80 dark:bg-white/3 p-1 rounded-xl border border-zinc-200/50 dark:border-white/4">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground transition-all hover:bg-white dark:hover:bg-white/10 shadow-sm outline-none focus-ring"
                aria-label="Toggle theme"
              >
                {resolvedTheme === 'dark' ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              </button>
              <a
                href="https://github.com/Anurag-Basuri"
                target="_blank"
                rel="noreferrer"
                className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground hover:text-foreground transition-all hover:bg-white dark:hover:bg-white/10 shadow-sm outline-none focus-ring"
              >
                <Icons.Github className="h-3.5 w-3.5" />
              </a>
            </div>

            {/* Links for logged in users */}
            <AnimatePresence>
              {session && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="hidden md:block"
                >
                  <Link
                    href="/chat"
                    className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:text-primary/80 transition-colors bg-primary/10 px-3 py-1.5 rounded-lg outline-none focus-ring"
                  >
                    Console <Icons.ChevronDown className="h-3 w-3 -rotate-90" />
                  </Link>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="h-4 w-px bg-zinc-200 dark:bg-white/10 hidden md:block" />

            {/* Auth Button */}
            <AuthButton className="rounded-xl shadow-sm h-9 px-4 text-xs font-semibold" />
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
