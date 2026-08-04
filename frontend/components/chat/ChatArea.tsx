'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { MessageBubble } from './MessageBubble';
import { SuggestionChips } from './SuggestionChips';
import { Icons } from '../ui/Icons';

export function ChatArea() {
  const { messages, isTyping, isAdmin } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="flex flex-1 flex-col items-center justify-center p-8 text-center"
      >
        <div className="relative mb-10 group">
          <div className="absolute inset-0 rounded-full bg-primary/20 blur-[60px] opacity-50 group-hover:opacity-80 transition-opacity duration-700" />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl glass-card animate-float shadow-2xl shadow-primary/10">
            <Icons.Agent className="h-10 w-10 text-primary" />
          </div>
        </div>
        <h2 className="text-4xl font-black text-foreground mb-4 font-display tracking-tight">
          Ready to assist{isAdmin ? ', Admin.' : '.'}
        </h2>
        <p className="max-w-md text-muted-foreground text-sm leading-relaxed mb-8 text-balance">
          {isAdmin 
            ? 'Full system access granted. You can query MCP servers, view system health, or adjust global settings.'
            : 'Ask me about the technical roadmap, portfolio data, or have me trigger safe external tool workflows.'}
        </p>
        <SuggestionChips />
      </motion.div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-0 scroll-smooth">
      <div className="mx-auto max-w-3xl w-full py-10 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg, index) => (
            <motion.div
              key={msg.id || index}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, transition: { duration: 0.2 } }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            >
              <MessageBubble message={msg} />
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-4 p-2"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary shadow-inner">
              <Icons.Agent className="h-5 w-5" />
            </div>
            <div className="flex items-center gap-3 px-5 py-3 glass-card rounded-3xl rounded-tl-sm shadow-sm">
              {typeof isTyping === 'string' && (
                <span className="text-xs font-semibold text-primary/90 tracking-wide font-mono">
                  {isTyping}
                </span>
              )}
              <div className="flex items-center gap-1.5 h-full">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} className="h-24" />
      </div>
    </div>
  );
}
