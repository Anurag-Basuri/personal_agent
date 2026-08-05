'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';
import Link from 'next/link';
import Image from 'next/image';
import { ConfirmDialog } from '../ui/ConfirmDialog';

function formatRelativeTime(timestamp: string): string {
	const date = new Date(timestamp);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffMins = Math.floor(diffMs / 60000);
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);

	if (diffMins < 1) return 'Just now';
	if (diffMins < 60) return `${diffMins}m ago`;
	if (diffHours < 24) return `${diffHours}h ago`;
	if (diffDays < 7) return `${diffDays}d ago`;
	return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function groupMessagesByDay(messages: { role: string; content: string; timestamp: string }[]) {
	const userMessages = messages.filter(m => m.role === 'user');
	if (userMessages.length === 0) return { today: [], earlier: [] };

	const now = new Date();
	const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

	const today: typeof userMessages = [];
	const earlier: typeof userMessages = [];

	for (const msg of userMessages) {
		const msgDate = new Date(msg.timestamp);
		if (msgDate >= todayStart) {
			today.push(msg);
		} else {
			earlier.push(msg);
		}
	}

	return { today: today.reverse(), earlier: earlier.reverse() };
}

export function Sidebar() {
	const {
		isSidebarOpen,
		setSidebarOpen,
		messages,
		isAdmin,
	} = useAgentStore();
	
	const { resetSession, deleteAll } = useAgentAPI();
	
	const [showResetConfirm, setShowResetConfirm] = useState(false);
	const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

	const grouped = useMemo(() => groupMessagesByDay(messages), [messages]);
	const hasMessages = messages.length > 0;

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
				<div className="flex h-full w-70 flex-col p-5">
					{/* Brand */}
					<div className="mb-6">
						<Link href="/" className="flex items-center gap-2.5 px-2 group outline-none rounded-md focus-ring">
							<div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-[#1E1E1E] border border-zinc-800 shadow-sm overflow-hidden group-hover:border-primary/50 transition-colors">
								<Image src="/logo.png" alt="Cortex Logo" width={24} height={24} priority className="object-contain drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]" />
							</div>
							<span className="font-display text-lg font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">Anurag's Cortex</span>
						</Link>
					</div>

					{/* Recent Conversations */}
					<div className="flex-1 overflow-y-auto space-y-4 min-h-0">
						{hasMessages ? (
							<>
								{grouped.today.length > 0 && (
									<div>
										<div className="px-2 mb-2">
											<span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 font-mono">
												Today
											</span>
										</div>
										<div className="space-y-0.5">
											{grouped.today.slice(0, 10).map((msg, i) => (
												<div
													key={`today-${i}`}
													className="flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-sm transition hover:bg-zinc-100 dark:hover:bg-white/4 cursor-default"
												>
													<Icons.Chat className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground/50" />
													<div className="flex-1 min-w-0">
														<p className="text-[13px] text-foreground truncate leading-snug">
															{msg.content.length > 40 ? msg.content.slice(0, 40) + '...' : msg.content}
														</p>
														<span className="text-[10px] text-muted-foreground/50 font-mono">
															{formatRelativeTime(msg.timestamp)}
														</span>
													</div>
												</div>
											))}
										</div>
									</div>
								)}

								{grouped.earlier.length > 0 && (
									<div>
										<div className="px-2 mb-2">
											<span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 font-mono">
												Earlier
											</span>
										</div>
										<div className="space-y-0.5">
											{grouped.earlier.slice(0, 15).map((msg, i) => (
												<div
													key={`earlier-${i}`}
													className="flex items-start gap-2.5 rounded-lg px-2.5 py-2 text-sm transition hover:bg-zinc-100 dark:hover:bg-white/4 cursor-default"
												>
													<Icons.Chat className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground/50" />
													<div className="flex-1 min-w-0">
														<p className="text-[13px] text-foreground truncate leading-snug">
															{msg.content.length > 40 ? msg.content.slice(0, 40) + '...' : msg.content}
														</p>
														<span className="text-[10px] text-muted-foreground/50 font-mono">
															{formatRelativeTime(msg.timestamp)}
														</span>
													</div>
												</div>
											))}
										</div>
									</div>
								)}
							</>
						) : (
							<div className="flex flex-col items-center justify-center py-12 px-4 text-center">
								<div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/8 mb-3">
									<Icons.Chat className="h-4.5 w-4.5 text-primary/50" />
								</div>
								<p className="text-[13px] font-medium text-muted-foreground/70 mb-1">No conversations yet</p>
								<p className="text-[11px] text-muted-foreground/40 leading-relaxed">
									Send a message to start chatting with Cortex
								</p>
							</div>
						)}
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
