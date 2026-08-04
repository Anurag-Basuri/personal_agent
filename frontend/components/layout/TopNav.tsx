'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { Icons } from '../ui/Icons';
import { AuthButton } from '../auth/AuthButton';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon } from 'lucide-react';
import { cn } from '@/utils/cn';

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
      <div className="glass flex h-16 w-full max-w-5xl items-center justify-between gap-6 rounded-full px-4 md:px-6 shadow-2xl pointer-events-auto">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group focus-ring rounded-xl outline-none">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-lg animate-glow group-hover:scale-105 transition-transform">
            <Icons.Agent className="h-5 w-5" />
          </div>
          <span className="font-display text-xl font-bold tracking-tight text-foreground hidden sm:block">
            Personal Agent
          </span>
        </Link>

        {/* Actions */}
        <div className="flex items-center gap-3 md:gap-5">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary/50 text-foreground transition-colors hover:bg-secondary focus-ring outline-none"
            aria-label="Toggle theme"
          >
            {resolvedTheme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
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

          <div className="h-6 w-px bg-border hidden md:block" />

          {/* Auth Button */}
          <AuthButton className="rounded-full shadow-md" />
        </div>
      </div>
    </motion.nav>
  );
}
