'use client';

import { motion } from 'framer-motion';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

interface HealthCardProps {
  title: string;
  status: 'operational' | 'degraded' | 'offline';
  description?: string;
  icon?: React.ReactNode;
}

export function HealthCard({ title, status, description, icon }: HealthCardProps) {
  const isOperational = status === 'operational';
  const isDegraded = status === 'degraded';

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="glass-card rounded-2xl p-5 flex flex-col justify-between h-full border border-border/50"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl",
            isOperational ? "bg-success/10 text-success" : 
            isDegraded ? "bg-warning/10 text-warning" : "bg-destructive/10 text-destructive"
          )}>
            {icon || <Icons.Settings className="h-5 w-5" />}
          </div>
          <h3 className="font-semibold text-foreground tracking-tight">{title}</h3>
        </div>
        <div className={cn(
          "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border font-mono",
          isOperational ? "bg-success/10 text-success border-success/20" : 
          isDegraded ? "bg-warning/10 text-warning border-warning/20" : "bg-destructive/10 text-destructive border-destructive/20"
        )}>
          {status}
        </div>
      </div>
      
      {description && (
        <p className="text-sm text-muted-foreground leading-relaxed mt-2">
          {description}
        </p>
      )}
    </motion.div>
  );
}
