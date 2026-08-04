'use client';

import { ToolCall } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

export function ToolCallBadge({ tool }: { tool: ToolCall }) {
  const isPending = tool.state === 'pending';
  const isError = tool.state === 'error';

  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-all',
        isPending
          ? 'border-warning/30 bg-warning/10 text-warning'
          : isError
            ? 'border-destructive/30 bg-destructive/10 text-destructive'
            : 'border-success/30 bg-success/10 text-success',
      )}
    >
      <Icons.Tool className={cn('h-4 w-4', isPending && 'animate-spin text-warning')} />
      <span className="font-mono text-xs font-semibold tracking-wide">{tool.name}</span>
      {isPending && <span className="text-xs opacity-70 font-mono">Running...</span>}
      {isError && <span className="text-xs text-destructive font-mono">Failed</span>}
      {!isPending && !isError && <Icons.Check className="h-4 w-4 text-success ml-auto" />}
    </div>
  );
}
