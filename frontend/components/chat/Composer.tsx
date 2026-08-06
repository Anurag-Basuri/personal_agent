'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { useAgentStore } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';

export function Composer() {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage } = useAgentAPI();
  const { isTyping } = useAgentStore();

  const adjustHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    requestAnimationFrame(adjustHeight);
  };

  const handleSubmit = () => {
    if (!text.trim() || isTyping) return;
    sendMessage(text.trim());
    setText('');
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.focus();
      }
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-zinc-200/80 dark:border-white/6 bg-white/60 dark:bg-zinc-950/40 backdrop-blur-xl">
      <div className="mx-auto w-full max-w-3xl px-4 md:px-6 py-3">
        <div className="relative flex items-end gap-2 p-1.5 rounded-2xl bg-zinc-50 dark:bg-white/3 border border-zinc-200 dark:border-white/6 transition-all focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary/40 focus-within:bg-white dark:focus-within:bg-white/5 group">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            autoFocus={true}
            placeholder="Message Agent..."
            className="max-h-50 min-h-11 w-full resize-none border-0 bg-transparent py-3 pl-3.5 pr-14 text-[15px] focus:ring-0 placeholder:text-muted-foreground/40 transition-all font-medium outline-none text-foreground"
          />

          <AnimatePresence>
            {text.trim() && !isTyping && (
              <>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute right-15 bottom-4.5 hidden sm:flex items-center gap-1.5 pointer-events-none"
                >
                  <span className="text-[10px] font-medium text-muted-foreground/50 font-mono flex items-center">
                    <span className="bg-zinc-200/80 dark:bg-white/10 px-1.5 py-0.5 rounded mr-1 text-muted-foreground/60">↵</span>
                    to send
                  </span>
                </motion.div>
              <motion.button
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                onClick={handleSubmit}
                className="absolute right-3 bottom-3 flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all active:scale-90 focus-ring outline-none"
              >
                <Icons.Send className="h-4 w-4" />
              </motion.button>
              </>
            )}
          </AnimatePresence>

          {!text.trim() && (
            <div className="absolute right-3 bottom-3 flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-200/60 dark:bg-muted/50 text-muted-foreground/30 dark:text-muted-foreground/40">
              <Icons.Send className="h-4 w-4" />
            </div>
          )}
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-2 text-center text-[10px] font-medium uppercase tracking-widest text-muted-foreground/30 dark:text-muted-foreground/40 font-mono"
        >
          Secure Workspace &bull; RAG Context Active &bull; AES-GCM Encrypted
        </motion.p>
      </div>
    </div>
  );
}
