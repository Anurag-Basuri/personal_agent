'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';
import Link from 'next/link';
import Image from 'next/image';
import { ConfirmDialog } from '../ui/ConfirmDialog';

export function Sidebar() {
	const {
		isSidebarOpen,
		setSidebarOpen,
		isAdmin,
	} = useAgentStore();
	
	const { resetSession, deleteAll } = useAgentAPI();
	
	const [showResetConfirm, setShowResetConfirm] = useState(false);
	const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

	const handleReset = async () => {
		await resetSession();
		if (window.innerWidth < 768) setSidebarOpen(false);
	};

	const handleDeleteAll = async () => {
		await deleteAll();
		if (window.innerWidth < 768) setSidebarOpen(false);
	};

	return (
		<>
			{/* Mobile Overlay */}
			<AnimatePresence>
				{isSidebarOpen && (
					<motion.div
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						exit={{ opacity: 0 }}
						onClick={() => setSidebarOpen(false)}
						className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
					/>
				)}
			</AnimatePresence>

			{/* Sidebar Container */}
			<motion.div
				initial={false}
				animate={{
					width: isSidebarOpen ? 280 : 0,
					opacity: isSidebarOpen ? 1 : 0,
				}}
				transition={{ type: 'spring', damping: 25, stiffness: 200 }}
				className={cn(
					'fixed inset-y-0 left-0 z-50 flex h-full flex-col overflow-hidden',
					'bg-white dark:bg-zinc-950/60 backdrop-blur-2xl border-r border-zinc-200 dark:border-white/6',
					'md:relative shadow-2xl md:shadow-none',
					!isSidebarOpen && 'md:w-0',
				)}
			>
				<div className="flex h-full w-70 flex-col p-5 space-y-6">
					{/* Brand */}
					<div className="space-y-4">
						<Link href="/" className="flex items-center gap-2.5 px-2 group outline-none rounded-md focus-ring">
							<div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-[#1E1E1E] border border-zinc-800 shadow-sm overflow-hidden group-hover:border-primary/50 transition-colors">
								<Image src="/logo.png" alt="Cortex Logo" width={24} height={24} className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
							</div>
							<span className="font-display text-lg font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">Anurag's Cortex</span>
						</Link>
					</div>

					{/* Capabilities Info */}
					<div className="flex-1 space-y-6 pt-4">
						<div className="px-2">
							<span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 font-mono">
								Capabilities
							</span>
						</div>
						
						<div className="space-y-4 px-2">
							<div className="flex gap-3">
								<div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-secondary/10 text-secondary">
									<Icons.Tool className="h-3.5 w-3.5" />
								</div>
								<div>
									<h4 className="text-sm font-semibold text-foreground">Tool Orchestration</h4>
									<p className="text-xs font-medium text-muted-foreground/80 leading-relaxed mt-0.5 text-balance">
										Autonomous tool execution via MCP and local APIs.
									</p>
								</div>
							</div>
							
							<div className="flex gap-3">
								<div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-accent/10 text-accent">
									<Icons.Check className="h-3.5 w-3.5" />
								</div>
								<div>
									<h4 className="text-sm font-semibold text-foreground">Persistent Memory</h4>
									<p className="text-xs font-medium text-muted-foreground/80 leading-relaxed mt-0.5 text-balance">
										Summarizes conversations and stores facts via RAG.
									</p>
								</div>
							</div>

							<div className="flex gap-3">
								<div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
									<Icons.Chat className="h-3.5 w-3.5" />
								</div>
								<div>
									<h4 className="text-sm font-semibold text-foreground">Continuous Context</h4>
									<p className="text-xs font-medium text-muted-foreground/80 leading-relaxed mt-0.5 text-balance">
										Single-thread architecture means context is never lost.
									</p>
								</div>
							</div>
						</div>
					</div>

					{/* Footer Controls */}
					<div className="pt-4 border-t border-zinc-200 dark:border-white/6 flex flex-col gap-1.5">
						<button 
							onClick={() => setShowResetConfirm(true)}
							className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-zinc-100 dark:hover:bg-white/4 hover:text-foreground focus-ring outline-none"
						>
							<Icons.Reset className="h-4 w-4 opacity-50 transition-transform group-hover:rotate-180" />
							Clear Agent Memory
						</button>
						<button
							onClick={() => setShowDeleteConfirm(true)}
							className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-destructive/80 transition hover:bg-destructive/10 hover:text-destructive focus-ring outline-none"
						>
							<Icons.Delete className="h-4 w-4 opacity-60 transition-colors group-hover:text-destructive" />
							Delete All Data
						</button>
					</div>
				</div>
			</motion.div>

			<ConfirmDialog
				isOpen={showResetConfirm}
				title="Clear Agent Memory?"
				message="This will clear the agent's short-term memory (summaries and context). Your message history will remain visible."
				confirmText="Clear Memory"
				onConfirm={handleReset}
				onCancel={() => setShowResetConfirm(false)}
			/>

			<ConfirmDialog
				isOpen={showDeleteConfirm}
				title="Delete All Data?"
				message="This will permanently delete all your messages, summaries, and learned preferences. This action cannot be undone."
				confirmText="Delete Everything"
				isDestructive={true}
				onConfirm={handleDeleteAll}
				onCancel={() => setShowDeleteConfirm(false)}
			/>
		</>
	);
}
