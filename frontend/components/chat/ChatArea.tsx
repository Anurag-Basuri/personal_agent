'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { MessageBubble } from './MessageBubble';
import { SuggestionChips } from './SuggestionChips';
import Image from 'next/image';

export function ChatArea() {
  const { messages, isStreaming, streamingMessageId, isAdmin } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 150;
    setIsAutoScroll(isAtBottom);
  };

  // Auto-scroll during streaming and new messages
  useEffect(() => {
    if (isAutoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming, isAutoScroll]);

  // Higher frequency auto-scroll during active streaming for smooth follow
  useEffect(() => {
    if (!isStreaming || !isAutoScroll) return;

    const interval = setInterval(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 300);

    return () => clearInterval(interval);
  }, [isStreaming, isAutoScroll]);

  if (messages.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="flex flex-1 flex-col items-center justify-center p-8 text-center"
      >
        <div className="relative mb-10 group">
          <div className="absolute inset-0 rounded-full bg-primary/10 dark:bg-primary/20 blur-[60px] opacity-50 group-hover:opacity-80 transition-opacity duration-700" />
          <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-lg animate-float overflow-hidden">
            <Image src="/logo.png" alt="Cortex Logo" width={50} height={50} priority className="object-contain drop-shadow-[0_0_12px_rgba(139,92,246,0.6)]" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-foreground mb-3 font-display tracking-tight">
          Cortex is online{isAdmin ? ', Admin.' : '.'}
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
    <div 
      ref={scrollRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 md:px-0 scroll-smooth"
    >
      <div className="mx-auto max-w-3xl w-full py-10 space-y-2">
        <AnimatePresence initial={false}>
          {messages.map((msg, index) => (
            <motion.div
              key={msg.id || index}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, transition: { duration: 0.2 } }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            >
              <MessageBubble
                message={msg}
                isStreaming={isStreaming && msg.id === streamingMessageId}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        <div ref={bottomRef} className="h-24" />
      </div>
    </div>
  );
}
