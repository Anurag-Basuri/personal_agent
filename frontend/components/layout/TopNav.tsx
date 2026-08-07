'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import Image from 'next/image';
import { Icons } from '../ui/Icons';
import { AuthButton } from '../auth/AuthButton';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon, Linkedin, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';

const SOCIAL_LINKS = [
  { href: 'https://anuragbasuri.vercel.app/portfolio', label: 'Portfolio', icon: ExternalLink },
  { href: 'https://github.com/Anurag-Basuri', label: 'GitHub', icon: Icons.Github },
  { href: 'https://www.linkedin.com/in/anuragbasuri/', label: 'LinkedIn', icon: Linkedin },
];

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
        <div className="relative flex h-14 w-full items-center justify-between gap-4 rounded-2xl px-4 md:px-6 bg-white/90 dark:bg-zinc-950/80 backdrop-blur-2xl border border-zinc-200/50 dark:border-white/5 shadow-xl">
          {/* Left: Brand */}
          <Link href="/" className="flex items-center gap-2.5 outline-none rounded-lg focus-ring shrink-0">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden hover:border-primary/50 transition-colors">
              <Image src="/logo.png" alt="Cortex Logo" width={24} height={24} priority className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
            </div>
            <span className="font-display text-[15px] font-bold tracking-tight text-foreground hidden sm:block hover:text-primary transition-colors">
              Anurag&apos;s Cortex
            </span>
          </Link>

          {/* Center: Social Links (hidden on mobile) */}
          <div className="hidden md:flex items-center gap-1">
            {SOCIAL_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-muted-foreground hover:text-foreground hover:bg-zinc-100 dark:hover:bg-white/5 transition-all outline-none focus-ring"
              >
                <link.icon className="h-3.5 w-3.5" />
                <span>{link.label}</span>
              </a>
            ))}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="relative flex h-8 w-14 items-center rounded-full bg-zinc-200/50 dark:bg-black/50 border border-zinc-200 dark:border-white/10 shadow-inner transition-colors focus-ring outline-none overflow-hidden"
              aria-label="Toggle theme"
            >
              <div className={cn(
                "absolute inset-y-0.5 w-7 rounded-full bg-white dark:bg-zinc-700 shadow-sm transition-all duration-300 ease-in-out",
                resolvedTheme === 'dark' ? "left-[calc(100%-1.875rem)]" : "left-0.5"
              )} />
              <div className="absolute left-0.5 inset-y-0.5 w-7 flex items-center justify-center z-10 pointer-events-none">
                <Sun className={cn("h-3.5 w-3.5 transition-colors", resolvedTheme === 'dark' ? "text-muted-foreground/50" : "text-amber-500")} />
              </div>
              <div className="absolute right-0.5 inset-y-0.5 w-7 flex items-center justify-center z-10 pointer-events-none">
                <Moon className={cn("h-3.5 w-3.5 transition-colors", resolvedTheme === 'dark' ? "text-indigo-400" : "text-muted-foreground/50")} />
              </div>
            </button>

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
