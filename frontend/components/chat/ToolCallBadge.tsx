'use client';

import { useState } from 'react';
import { ToolCall } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';

export function ToolCallBadge({ tool }: { tool: ToolCall }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isPending = tool.state === 'pending';
  const isError = tool.state === 'error';

  return (
    <div className="flex flex-col w-full mb-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs transition-all w-fit',
          isPending
            ? 'border-amber-300 dark:border-warning/30 bg-amber-50 dark:bg-warning/10 text-amber-700 dark:text-warning'
            : isError
              ? 'border-red-200 dark:border-destructive/30 bg-red-50 dark:bg-destructive/10 text-red-700 dark:text-destructive'
              : 'border-emerald-200 dark:border-success/30 bg-emerald-50 dark:bg-success/10 text-emerald-700 dark:text-success',
          'hover:opacity-80 active:scale-[0.98] outline-none cursor-pointer'
        )}
      >
        <Icons.Tool className={cn('h-3.5 w-3.5', isPending && 'animate-spin')} />
        <span className="font-mono font-semibold tracking-wide">{tool.name}</span>
        {isPending && <span className="opacity-70 font-mono">Running...</span>}
        {isError && <span className="font-mono">Failed</span>}
        {!isPending && !isError && <Icons.Check className="h-3.5 w-3.5 ml-1" />}
        <Icons.ChevronDown className={cn('h-3.5 w-3.5 ml-2 transition-transform', isExpanded && 'rotate-180')} />
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-2 p-3 bg-[#1E1E1E] rounded-xl border border-zinc-800 shadow-inner max-w-full">
              <div className="text-xs font-mono text-zinc-400 mb-1">Arguments:</div>
              <pre className="text-[11px] text-zinc-300 overflow-x-auto p-2 bg-black/40 rounded-lg">
                {typeof tool.args === 'string' ? tool.args : JSON.stringify(tool.args, null, 2)}
              </pre>
              
              {tool.result && (
                <>
                  <div className="text-xs font-mono text-zinc-400 mt-3 mb-1">Result:</div>
                  <pre className="text-[11px] text-zinc-300 overflow-x-auto p-2 bg-black/40 rounded-lg whitespace-pre-wrap">
                    {tool.result}
                  </pre>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
