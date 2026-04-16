'use client';

import { motion } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';

export function Header() {
	const { isSidebarOpen, setSidebarOpen } = useAgentStore();

	return (
		<header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/70 px-6 backdrop-blur-xl">
			<div className="flex items-center gap-4">
				<button
					onClick={() => setSidebarOpen(!isSidebarOpen)}
					className="p-2 -ml-2 rounded-xl hover:bg-muted text-muted-foreground transition-colors duration-200"
				>
					<Icons.Menu className="h-5 w-5" />
				</button>
				<motion.div
					initial={{ opacity: 0, x: -10 }}
					animate={{ opacity: 1, x: 0 }}
					className="flex flex-col"
				>
					<span className="font-display text-base font-bold tracking-tight text-foreground">
						Neural Workspace
					</span>
					<span className="text-[10px] text-muted-foreground/60 font-black uppercase tracking-widest leading-none mt-0.5">
						Edge Computing &bull; V2.4.0
					</span>
				</motion.div>
			</div>

			<div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-primary/5 border border-primary/10 shadow-sm">
				<div className="relative">
					<div className="h-2 w-2 rounded-full bg-primary animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
					<div className="absolute inset-0 h-2 w-2 rounded-full bg-primary animate-ping opacity-25" />
				</div>
				<span className="text-[10px] font-black text-primary uppercase tracking-[0.2em]">
					Ready
				</span>
			</div>
		</header>
	);
}
