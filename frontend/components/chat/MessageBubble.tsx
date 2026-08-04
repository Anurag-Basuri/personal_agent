'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../../store/useAgentStore';
import { cn } from '../../utils/cn';
import { Icons } from '../ui/Icons';
import { ToolCallBadge } from './ToolCallBadge';
import { motion } from 'framer-motion';

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="mx-auto my-6 max-w-[90%] rounded-xl bg-destructive/10 px-6 py-3 text-center text-xs font-bold uppercase tracking-widest text-destructive border border-destructive/20 backdrop-blur-sm shadow-sm font-mono">
        <Icons.Warning className="inline-block h-4 w-4 mr-2 -mt-0.5" />
        System Alert: {message.content}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex w-full gap-3 sm:gap-4 py-4 sm:py-6 group',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl shadow-sm transition-transform group-hover:scale-105',
          isUser
            ? 'bg-muted border border-border text-foreground'
            : 'bg-primary text-primary-foreground shadow-primary/20 border border-primary/20',
        )}
      >
        {isUser ? <Icons.User className="h-5 w-5" /> : <Icons.Agent className="h-5 w-5" />}
      </div>

      {/* Bubble Content */}
      <div
        className={cn(
          'flex flex-col gap-1.5 max-w-[85%] sm:max-w-[80%]',
          isUser ? 'items-end' : 'items-start',
        )}
      >
        <div
          className={cn(
            'flex items-center gap-2 px-1 opacity-0 group-hover:opacity-100 transition-opacity',
            isUser ? 'flex-row-reverse' : 'flex-row',
          )}
        >
          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground font-mono">
            {isUser ? 'User' : 'Neural Agent v2.5'}
          </span>
          <span className="text-[10px] text-muted-foreground/40 font-mono">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <motion.div
          whileHover={{ y: -2 }}
          className={cn(
            'relative px-5 py-4 rounded-[24px] shadow-sm text-[15px] leading-relaxed transition-all',
            isUser
              ? 'bg-foreground text-background rounded-tr-sm font-medium'
              : 'glass-card rounded-tl-sm text-foreground',
          )}
        >
          {/* Markdown Content */}
          <div
            className={cn(
              'prose max-w-none break-words',
              isUser
                ? 'prose-invert prose-p:text-background'
                : 'prose-zinc dark:prose-invert',
            )}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>

          {/* Tool Executions */}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border/50">
              {message.toolCalls.map((tc) => (
                <ToolCallBadge key={tc.id} tool={tc} />
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
