'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../../store/useAgentStore';
import { cn } from '../../utils/cn';
import { Icons } from '../ui/Icons';
import { ToolCallBadge } from './ToolCallBadge';
import { CodeBlock } from './CodeBlock';
import { NeuralActivityFeed } from './NeuralActivityFeed';
import { StreamCursor } from './StreamCursor';
import { motion } from 'framer-motion';

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const hasContent = message.content && message.content.trim() !== '';
  const hasActivityLog = message.activityLog && message.activityLog.length > 0;

  // Skip rendering if no content AND no activity log (nothing to show)
  if (!hasContent && !hasActivityLog && !isStreaming) return null;

  if (isSystem) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mx-auto my-6 w-full max-w-2xl"
      >
        <div className="flex flex-col rounded-xl overflow-hidden border border-red-500/30 bg-red-50/50 dark:bg-zinc-900 shadow-[0_0_20px_-5px_rgba(239,68,68,0.15)]">
          <div className="flex items-center gap-2 bg-red-500/10 border-b border-red-500/20 px-4 py-2">
            <Icons.Warning className="h-4 w-4 text-red-400" />
            <span className="text-xs font-mono font-semibold uppercase tracking-widest text-red-400">
              System Alert
            </span>
          </div>
          <div className="p-4 overflow-x-auto">
            <pre className="text-[13px] font-mono text-red-600/90 dark:text-red-300/90 whitespace-pre-wrap">
              {message.content}
            </pre>
          </div>
        </div>
      </motion.div>
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
          'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-transform group-hover:scale-105',
          isUser
            ? 'bg-zinc-100 dark:bg-muted border border-zinc-200 dark:border-border text-foreground'
            : 'bg-primary text-primary-foreground shadow-md shadow-primary/20',
          isStreaming && !isUser && 'animate-pulse-glow',
        )}
      >
        {isUser ? <Icons.User className="h-4 w-4" /> : <Icons.Agent className="h-4 w-4" />}
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
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground font-mono">
            {isUser ? 'You' : 'Agent'}
          </span>
          <span className="text-[10px] text-muted-foreground/50 font-mono">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <motion.div
          whileHover={isStreaming ? undefined : { y: -1 }}
          className={cn(
            'relative rounded-2xl text-[15px] leading-relaxed',
            isUser
              ? 'px-5 py-4 bg-primary text-primary-foreground rounded-tr-sm shadow-md shadow-primary/15'
              : 'bg-white dark:bg-white/4 border border-zinc-200 dark:border-white/6 rounded-tl-sm shadow-sm text-foreground',
            // When streaming with no content yet, give a min width
            isStreaming && !hasContent && !isUser && 'min-w-70 sm:min-w-90',
          )}
          style={!isUser ? { padding: hasContent || hasActivityLog ? undefined : '1rem 1.25rem' } : undefined}
        >
          {/* Assistant bubble inner padding */}
          {!isUser && (
            <div className={cn(hasContent || hasActivityLog ? 'px-5 py-4' : '')}>
              {/* Neural Activity Feed */}
              {hasActivityLog && (
                <NeuralActivityFeed
                  activityLog={message.activityLog!}
                  isStreaming={isStreaming}
                />
              )}

              {/* Markdown Content */}
              {hasContent && (
                <div className="prose prose-zinc dark:prose-invert max-w-none wrap-break-word">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      a: ({ node, ...props }) => (
                        <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline" />
                      ),
                      code(props) {
                        const {children, className, node, inline, ...rest} = props
                        const match = /language-(\w+)/.exec(className || '')
                        return match ? (
                          <CodeBlock
                            language={match[1]}
                            value={String(children).replace(/\n$/, '')}
                          />
                        ) : (
                          <code {...rest} className={className}>
                            {children}
                          </code>
                        )
                      }
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                  {isStreaming && <StreamCursor />}
                </div>
              )}

              {/* Show cursor even when no content yet but streaming (between activity and first token) */}
              {isStreaming && !hasContent && hasActivityLog && (
                <div className="pt-1">
                  <StreamCursor />
                </div>
              )}

              {/* Tool Executions (for historical messages loaded from history) */}
              {message.toolCalls && message.toolCalls.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-zinc-200/50 dark:border-white/10">
                  {message.toolCalls.map((tc) => (
                    <ToolCallBadge key={tc.id} tool={tc} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* User message content */}
          {isUser && (
            <div className="prose prose-invert prose-p:text-white/90 max-w-none wrap-break-word">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline" />
                  ),
                  code(props) {
                    const {children, className, node, inline, ...rest} = props
                    const match = /language-(\w+)/.exec(className || '')
                    return match ? (
                      <CodeBlock
                        language={match[1]}
                        value={String(children).replace(/\n$/, '')}
                      />
                    ) : (
                      <code {...rest} className={className}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
