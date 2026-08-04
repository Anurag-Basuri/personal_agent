'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

interface MCPServerCardProps {
  name: string;
  config: any;
  status: string;
  onToggle: (name: string) => Promise<void>;
  onDelete: (name: string) => Promise<void>;
}

export function MCPServerCard({ name, config, status, onToggle, onDelete }: MCPServerCardProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  const isEnabled = config.enabled !== false;
  const isConnected = status === 'connected';
  const isError = status === 'error';

  const handleToggle = async () => {
    setIsToggling(true);
    await onToggle(name);
    setIsToggling(false);
  };

  const handleDelete = async () => {
    if (confirm(`Are you sure you want to delete MCP server '${name}'?`)) {
      setIsDeleting(true);
      await onDelete(name);
      setIsDeleting(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="glass-card rounded-2xl p-5 border border-border/50 relative overflow-hidden"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl transition-colors",
            !isEnabled ? "bg-muted text-muted-foreground" :
            isConnected ? "bg-success/10 text-success" : 
            isError ? "bg-destructive/10 text-destructive" : "bg-warning/10 text-warning"
          )}>
            <Icons.Tool className={cn("h-5 w-5", isToggling && "animate-spin")} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground tracking-tight flex items-center gap-2">
              {name}
              {!isEnabled && <span className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 rounded-sm">DISABLED</span>}
            </h3>
            <p className="text-xs text-muted-foreground font-mono mt-1">
              {config.transport || 'stdio'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Status Badge */}
          {isEnabled && (
            <div className={cn(
              "px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border font-mono flex items-center gap-1.5",
              isConnected ? "bg-success/10 text-success border-success/20" : 
              isError ? "bg-destructive/10 text-destructive border-destructive/20" : "bg-warning/10 text-warning border-warning/20"
            )}>
              <span className={cn(
                "h-1.5 w-1.5 rounded-full",
                isConnected ? "bg-success animate-pulse" : isError ? "bg-destructive" : "bg-warning"
              )} />
              {status}
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center justify-between pt-4 border-t border-border/50 mt-auto">
        <button
          onClick={handleToggle}
          disabled={isToggling}
          className={cn(
            "text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors outline-none focus-ring",
            isEnabled 
              ? "border-warning/30 text-warning hover:bg-warning/10" 
              : "border-success/30 text-success hover:bg-success/10"
          )}
        >
          {isToggling ? 'Wait...' : isEnabled ? 'Disable' : 'Enable'}
        </button>
        
        <button
          onClick={handleDelete}
          disabled={isDeleting || isToggling}
          className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors outline-none focus-ring"
          title="Delete Server"
        >
          <Icons.Delete className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  );
}
