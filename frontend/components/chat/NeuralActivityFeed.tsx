'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Icons } from '../ui/Icons';
import { ActivityLogEntry } from '../../store/useAgentStore';
import { cn } from '../../utils/cn';

const PHASE_ICONS: Record<string, React.ReactNode> = {
  'Routing intent': <Icons.Zap className="h-3.5 w-3.5" />,
  'Activating neural engine': <Icons.Brain className="h-3.5 w-3.5" />,
  'Executing tools': <Icons.Tool className="h-3.5 w-3.5" />,
  'Synthesizing response': <Icons.Activity className="h-3.5 w-3.5" />,
};

function getIcon(entry: ActivityLogEntry) {
  if (entry.type === 'tool_end') {
    return <Icons.CircleCheck className="h-3.5 w-3.5 text-emerald-500" />;
  }
  if (entry.type === 'tool_start') {
    return <Icons.Loader className="h-3.5 w-3.5 animate-spin" />;
  }
  return PHASE_ICONS[entry.label] || <Icons.Activity className="h-3.5 w-3.5" />;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function LiveTimer({ startTime }: { startTime: number }) {
  const [elapsed, setElapsed] = useState(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const tick = () => {
      setElapsed(Date.now() - startTime);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [startTime]);

  return (
    <span className="text-[10px] font-mono text-muted-foreground/60 tabular-nums">
      {formatDuration(elapsed)}
    </span>
  );
}

interface NeuralActivityFeedProps {
  activityLog: ActivityLogEntry[];
  isStreaming: boolean;
}

export function NeuralActivityFeed({ activityLog, isStreaming }: NeuralActivityFeedProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Auto-expand during streaming, auto-collapse when done
  useEffect(() => {
    if (isStreaming) {
      setIsExpanded(true);
    } else if (activityLog.length > 0) {
      const timer = setTimeout(() => setIsExpanded(false), 600);
      return () => clearTimeout(timer);
    }
  }, [isStreaming, activityLog.length]);

  if (!activityLog || activityLog.length === 0) return null;

  // Filter to only show meaningful entries (not duplicate tool_end for display)
  const displayEntries = activityLog.filter(e => e.type !== 'tool_end');
  const completedTools = activityLog.filter(e => e.type === 'tool_end');
  const totalToolTime = completedTools.reduce((sum, t) => sum + (t.duration || 0), 0);
  const toolCount = completedTools.length;

  // Mark tool_start entries as completed if we have a matching tool_end
  const completedToolNames = new Set(completedTools.map(t => t.label));

  return (
    <div className="mb-3">
      {/* Collapsed Summary */}
      {!isExpanded && (
        <motion.button
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={() => setIsExpanded(true)}
          className={cn(
            'flex items-center gap-2 w-full text-left px-3 py-2 rounded-xl',
            'bg-primary/[0.04] dark:bg-primary/[0.06] border border-primary/10 dark:border-primary/15',
            'hover:bg-primary/[0.07] dark:hover:bg-primary/[0.09] transition-colors cursor-pointer group',
          )}
        >
          <Icons.ChevronRight className="h-3 w-3 text-primary/50 group-hover:text-primary transition-colors" />
          <Icons.Brain className="h-3.5 w-3.5 text-primary/40" />
          <span className="text-[11px] font-medium text-muted-foreground">
            {toolCount > 0
              ? `${toolCount} tool${toolCount > 1 ? 's' : ''} used · ${formatDuration(totalToolTime)}`
              : `Processed in ${formatDuration(totalToolTime || (activityLog[activityLog.length - 1]?.timestamp - activityLog[0]?.timestamp) || 0)}`
            }
          </span>
        </motion.button>
      )}

      {/* Expanded Activity Log */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
            className="overflow-hidden"
          >
            <div
              className={cn(
                'rounded-xl border px-3 py-2.5',
                isStreaming
                  ? 'bg-primary/[0.03] dark:bg-primary/[0.05] border-primary/15 dark:border-primary/20'
                  : 'bg-zinc-50/50 dark:bg-white/[0.02] border-zinc-200/60 dark:border-white/6',
              )}
            >
              {/* Header */}
              <button
                onClick={() => !isStreaming && setIsExpanded(false)}
                className={cn(
                  'flex items-center gap-2 w-full text-left mb-2',
                  !isStreaming && 'cursor-pointer hover:opacity-70 transition-opacity',
                )}
                disabled={isStreaming}
              >
                {isStreaming ? (
                  <div className="relative h-2.5 w-2.5">
                    <div className="absolute inset-0 rounded-full bg-primary animate-ping opacity-40" />
                    <div className="relative h-2.5 w-2.5 rounded-full bg-primary" />
                  </div>
                ) : (
                  <Icons.ChevronDown className="h-3 w-3 text-muted-foreground/40" />
                )}
                <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/60 font-mono">
                  Neural Activity
                </span>
              </button>

              {/* Timeline */}
              <div className="space-y-1">
                <AnimatePresence initial={false}>
                  {displayEntries.map((entry, idx) => {
                    const isToolEntry = entry.type === 'tool_start';
                    const isCompleted = isToolEntry && completedToolNames.has(entry.label);
                    const isActive = isToolEntry && !isCompleted && isStreaming;
                    const isPhase = entry.type === 'status';

                    return (
                      <motion.div
                        key={`${entry.type}-${entry.label}-${idx}`}
                        initial={{ opacity: 0, x: -8, height: 0 }}
                        animate={{ opacity: 1, x: 0, height: 'auto' }}
                        transition={{
                          duration: 0.2,
                          ease: 'easeOut',
                        }}
                        className="flex items-center gap-2.5 py-1 overflow-hidden"
                      >
                        {/* Icon */}
                        <div
                          className={cn(
                            'flex-shrink-0 transition-colors',
                            isActive
                              ? 'text-primary animate-neural-pulse'
                              : isCompleted
                                ? 'text-emerald-500'
                                : isPhase
                                  ? 'text-primary/50'
                                  : 'text-muted-foreground/40',
                          )}
                        >
                          {isCompleted ? (
                            <Icons.CircleCheck className="h-3.5 w-3.5" />
                          ) : (
                            getIcon(entry)
                          )}
                        </div>

                        {/* Label */}
                        <span
                          className={cn(
                            'text-[12px] flex-1 min-w-0 truncate',
                            isActive
                              ? 'text-foreground/80 font-medium'
                              : isCompleted
                                ? 'text-muted-foreground/70'
                                : 'text-muted-foreground/60',
                            isToolEntry && 'font-mono',
                          )}
                        >
                          {isToolEntry ? (
                            <>
                              {isCompleted ? '' : 'Calling '}
                              <span className="font-semibold">{entry.label}</span>
                              {isCompleted ? ' completed' : '...'}
                            </>
                          ) : (
                            <>{entry.label}...</>
                          )}
                        </span>

                        {/* Duration or Live Timer */}
                        <div className="flex-shrink-0">
                          {isCompleted && entry.duration != null ? (
                            <span className="text-[10px] font-mono text-emerald-500/70 tabular-nums">
                              {formatDuration(entry.duration)}
                            </span>
                          ) : isActive ? (
                            <div className="flex items-center gap-1.5">
                              <LiveTimer startTime={entry.timestamp} />
                              <div className="w-12 h-1 rounded-full bg-primary/10 overflow-hidden">
                                <div className="h-full w-full rounded-full bg-gradient-to-r from-transparent via-primary/40 to-transparent animate-progress-sweep" />
                              </div>
                            </div>
                          ) : null}
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
