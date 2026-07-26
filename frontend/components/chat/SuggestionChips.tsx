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
		color: 'from-primary/20 to-secondary/20',
		hoverColor: 'group-hover:text-primary',
	},
	{
		title: 'Check GitHub metrics',
		prompt: 'What are your latest GitHub metrics and activity?',
		icon: <Icons.User className="h-5 w-5" />,
		color: 'from-secondary/20 to-primary/20',
		hoverColor: 'group-hover:text-secondary',
	},
	{
		title: 'Summarize notes',
		prompt: 'Please summarize my recent experience and skills.',
		icon: <Icons.Chat className="h-5 w-5" />,
		color: 'from-accent/20 to-primary/20',
		hoverColor: 'group-hover:text-accent',
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
			className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-3xl mx-auto mt-6"
		>
			{SUGGESTIONS.map((suggestion, idx) => (
				<motion.button
					key={idx}
					variants={itemVariants}
					whileHover={{ scale: 1.02, y: -2 }}
					whileTap={{ scale: 0.98 }}
					onClick={() => sendMessage(suggestion.prompt)}
					className={cn(
						'group relative overflow-hidden rounded-full border border-white/10 dark:border-zinc-800/50',
						'bg-card/30 p-4 text-left transition-all duration-300',
						'hover:bg-card/50 hover:shadow-xl hover:shadow-primary/5 hover:border-primary/30 backdrop-blur-xl'
					)}
				>
					<div
						className={`absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100 bg-gradient-to-br ${suggestion.color}`}
					/>
					<div className="relative z-10 flex items-center gap-3">
						<div className={cn('text-muted-foreground transition-colors duration-300', suggestion.hoverColor)}>
							{suggestion.icon}
						</div>
						<span className="font-semibold text-foreground text-sm tracking-wide line-clamp-1">
							{suggestion.title}
						</span>
					</div>
				</motion.button>
			))}
		</motion.div>
	);
}
