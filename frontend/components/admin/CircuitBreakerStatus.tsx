'use client';

import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface CircuitBreakerStatusProps {
  name: string;
  state: 'CLOSED' | 'HALF_OPEN' | 'OPEN';
  failureCount: number;
  failureThreshold: number;
}

export function CircuitBreakerStatus({ name, state, failureCount, failureThreshold }: CircuitBreakerStatusProps) {
  const isClosed = state === 'CLOSED'; // Normal operation
  const isHalfOpen = state === 'HALF_OPEN'; // Testing recovery
  const isOpen = state === 'OPEN'; // Failing, requests blocked

  return (
    <div className="flex items-center justify-between p-3 rounded-xl border border-border/50 bg-background/50">
      <div className="flex flex-col">
        <span className="font-mono text-sm font-semibold">{name}</span>
        <span className="text-xs text-muted-foreground mt-1">
          Failures: {failureCount} / {failureThreshold}
        </span>
      </div>
      
      <div className="flex items-center gap-2">
        <div className={cn(
          "h-2 w-2 rounded-full",
          isClosed ? "bg-success shadow-[0_0_8px_rgba(var(--success),0.8)] animate-pulse" :
          isHalfOpen ? "bg-warning shadow-[0_0_8px_rgba(var(--warning),0.8)]" :
          "bg-destructive shadow-[0_0_8px_rgba(var(--destructive),0.8)]"
        )} />
        <span className={cn(
          "text-xs font-bold font-mono tracking-widest",
          isClosed ? "text-success" :
          isHalfOpen ? "text-warning" :
          "text-destructive"
        )}>
          {state}
        </span>
      </div>
    </div>
  );
}
