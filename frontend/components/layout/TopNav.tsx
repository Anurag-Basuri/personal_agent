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
      <div className="flex h-14 w-full max-w-5xl items-center justify-between gap-6 rounded-2xl px-4 md:px-6 pointer-events-auto bg-white/80 dark:bg-zinc-950/60 backdrop-blur-xl border border-zinc-200/80 dark:border-white/[0.06] shadow-lg dark:shadow-2xl">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group focus-ring rounded-xl outline-none">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-[#1E1E1E] border border-zinc-800 shadow-sm overflow-hidden group-hover:border-primary/50 transition-colors">
            <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
          </div>
          <span className="font-display text-lg font-bold tracking-tight text-foreground hidden sm:block group-hover:text-primary transition-colors">
            Anurag's Cortex
          </span>
        </Link>

        {/* Actions */}
        <div className="flex items-center gap-2 md:gap-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-100 dark:bg-white/10 text-foreground transition-colors hover:bg-zinc-200 dark:hover:bg-white/20 focus-ring outline-none"
            aria-label="Toggle theme"
          >
            {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

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
                  className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
                >
                  Console &rarr;
                </Link>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="h-5 w-px bg-zinc-200 dark:bg-border hidden md:block" />

          {/* Auth Button */}
          <AuthButton className="rounded-xl shadow-sm" />
        </div>
      </div>
    </motion.nav>
  );
}
