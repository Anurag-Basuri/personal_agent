'use client';

import { useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';
import { Skeleton } from '../ui/Skeleton';
import Link from 'next/link';
import { useTheme } from '@/hooks/useTheme';
import { Sun, Moon } from 'lucide-react';

export function Sidebar() {
  const {
    isSidebarOpen,
    setSidebarOpen,
    sessions,
    sessionId,
    setSessionId,
    resetChat,
    isSessionsLoading,
  } = useAgentStore();
  const { fetchSessions, resetSession } = useAgentAPI();
  const { resolvedTheme, toggleTheme } = useTheme();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleNewChat = useCallback(async () => {
    await resetSession();
    resetChat();
    setSessionId(crypto.randomUUID());
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, [resetSession, resetChat, setSessionId, setSidebarOpen]);

  const loadSession = useCallback(
    (id: string) => {
      setSessionId(id);
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    },
    [setSessionId, setSidebarOpen],
  );

  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-md md:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar Container */}
      <motion.div
        initial={false}
        animate={{
          width: isSidebarOpen ? 280 : 0,
          opacity: isSidebarOpen ? 1 : 0,
        }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex h-full flex-col overflow-hidden bg-card/80 backdrop-blur-xl border-r border-border md:relative shadow-xl md:shadow-none',
          !isSidebarOpen && 'md:w-0',
        )}
      >
        <div className="flex h-full w-70 flex-col p-5 space-y-6">
          {/* Brand & New Chat */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-3 px-2 group outline-none rounded-md focus-ring">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                <Icons.Agent className="h-4 w-4" />
              </div>
              <span className="font-display text-lg font-bold tracking-tight">Agent Console</span>
            </Link>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleNewChat}
              className="flex w-full items-center justify-center gap-3 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg shadow-primary/20 transition-all hover:bg-primary/90 focus-ring outline-none"
            >
              <Icons.Add className="h-4 w-4" />
              Start New Cycle
            </motion.button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 -mr-1">
            <div className="px-2">
              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 font-mono">
                Recent Contexts
              </span>
            </div>

            <div className="flex flex-col gap-1.5">
              {isSessionsLoading ? (
                <div className="space-y-2 px-2">
                  <Skeleton className="h-11 w-full rounded-xl bg-muted/50" />
                  <Skeleton className="h-11 w-full rounded-xl bg-muted/30" />
                  <Skeleton className="h-11 w-full rounded-xl bg-muted/10" />
                </div>
              ) : sessions.length === 0 ? (
                <p className="px-2 text-xs text-muted-foreground/40 italic">
                  No previous logs found...
                </p>
              ) : (
                sessions.map((s) => (
                  <motion.button
                    key={s.id}
                    onClick={() => loadSession(s.sessionId)}
                    className={cn(
                      'group flex items-center gap-3 w-full truncate rounded-xl px-3 py-2.5 text-sm transition-all border outline-none focus-ring',
                      s.sessionId === sessionId
                        ? 'bg-primary/10 text-primary border-primary/20 shadow-sm'
                        : 'text-muted-foreground border-transparent hover:bg-muted/50 hover:text-foreground',
                    )}
                  >
                    <Icons.Chat
                      className={cn(
                        'h-4 w-4 shrink-0 transition-colors',
                        s.sessionId === sessionId
                          ? 'text-primary'
                          : 'text-muted-foreground/40 group-hover:text-muted-foreground',
                      )}
                    />
                    <div className="flex flex-col items-start truncate w-full">
                      <span className="truncate font-semibold text-sm">
                        Session_{s.sessionId.slice(0, 8)}
                      </span>
                      <span className="text-[10px] opacity-60 font-mono">
                        {new Date(s.createdAt).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    </div>
                  </motion.button>
                ))
              )}
            </div>
          </div>

          {/* Footer Controls */}
          <div className="pt-4 border-t border-border/50 flex flex-col gap-1.5">
            <button 
              onClick={toggleTheme}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground focus-ring outline-none"
            >
              {resolvedTheme === 'dark' ? <Sun className="h-4 w-4 opacity-50" /> : <Moon className="h-4 w-4 opacity-50" />}
              {resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </button>
            <a
              href="https://github.com/Anurag-Basuri"
              target="_blank"
              rel="noreferrer"
              className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground focus-ring outline-none"
            >
              <Icons.User className="h-4 w-4 opacity-50 transition-colors group-hover:text-primary" />
              Portfolio Access
            </a>
          </div>
        </div>
      </motion.div>
    </>
  );
}
