'use client';

import { motion, Variants } from 'framer-motion';
import { Icons } from '../ui/Icons';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { cn } from '../../utils/cn';

const SUGGESTIONS = [
  {
    title: 'Show my projects',
    prompt: 'Can you show me an overview of your best projects?',
    icon: <Icons.Tool className="h-5 w-5" />,
    accentClass: 'group-hover:text-primary group-hover:border-primary/20',
  },
  {
    title: 'Check GitHub metrics',
    prompt: 'What are your latest GitHub metrics and activity?',
    icon: <Icons.User className="h-5 w-5" />,
    accentClass: 'group-hover:text-secondary group-hover:border-secondary/20',
  },
  {
    title: 'Summarize experience',
    prompt: 'Please summarize my recent experience and skills.',
    icon: <Icons.Chat className="h-5 w-5" />,
    accentClass: 'group-hover:text-accent group-hover:border-accent/20',
  },
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { type: 'spring', stiffness: 200, damping: 20 } 
  },
};

export function SuggestionChips() {
  const { sendMessage } = useAgentAPI();

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-2xl mx-auto mt-6"
    >
      {SUGGESTIONS.map((suggestion, idx) => (
        <motion.button
          key={idx}
          variants={itemVariants}
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => sendMessage(suggestion.prompt)}
          className={cn(
            'group flex items-center gap-3 rounded-xl border border-zinc-200 dark:border-zinc-800/50',
            'bg-white dark:bg-white/2 px-4 py-3.5 text-left transition-all duration-200',
            'hover:shadow-md hover:border-zinc-300 dark:hover:border-primary/30',
            suggestion.accentClass,
          )}
        >
          <div className="text-muted-foreground transition-colors duration-200">
            {suggestion.icon}
          </div>
          <span className="font-medium text-foreground text-sm line-clamp-1">
            {suggestion.title}
          </span>
        </motion.button>
      ))}
    </motion.div>
  );
}
