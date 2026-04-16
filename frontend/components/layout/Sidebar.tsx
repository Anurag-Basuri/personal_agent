'use client';

import { useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';
import { Skeleton } from '../ui/Skeleton';

export function Sidebar() {
	const {
		isSidebarOpen,
		setSidebarOpen,
		sessions,
		sessionId,
		setSessionId,
		resetChat,
		isSessionsLoading,
	} = useAgentStore();
	const { fetchSessions, resetSession } = useAgentAPI();

	useEffect(() => {
		fetchSessions();
	}, [fetchSessions]);

	const handleNewChat = useCallback(async () => {
		await resetSession();
		resetChat();
		setSessionId(crypto.randomUUID());
		if (window.innerWidth < 768) {
			setSidebarOpen(false);
		}
	}, [resetSession, resetChat, setSessionId, setSidebarOpen]);

	const loadSession = useCallback(
		(id: string) => {
			setSessionId(id);
			if (window.innerWidth < 768) {
				setSidebarOpen(false);
			}
		},
		[setSessionId, setSidebarOpen],
	);

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
						className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
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
				className={cn(
					'fixed inset-y-0 left-0 z-50 flex h-full flex-col overflow-hidden bg-background border-r border-border md:relative',
					!isSidebarOpen && 'md:w-0',
				)}
			>
				<div className="flex h-full w-[280px] flex-col p-6 space-y-8">
					{/* New Chat Button */}
					<motion.button
						whileHover={{ scale: 1.02 }}
						whileTap={{ scale: 0.98 }}
						onClick={handleNewChat}
						className="flex items-center justify-center gap-3 rounded-2xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-lg animate-glow transition-all hover:bg-primary/90"
					>
						<Icons.Add className="h-4 w-4" />
						Start New Cycle
					</motion.button>

					{/* Sessions List */}
					<div className="flex-1 overflow-y-auto space-y-6">
						<div className="px-2">
							<span className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60 font-display">
								Recent Contexts
							</span>
						</div>

						<div className="flex flex-col gap-2">
							{isSessionsLoading ? (
								<div className="space-y-3 px-2">
									<Skeleton className="h-10 w-full rounded-xl" />
									<Skeleton className="h-10 w-full rounded-xl opacity-70" />
									<Skeleton className="h-10 w-full rounded-xl opacity-40" />
								</div>
							) : sessions.length === 0 ? (
								<p className="px-2 text-xs text-muted-foreground/40 italic">
									No previous logs found...
								</p>
							) : (
								sessions.map(s => (
									<motion.button
										key={s.id}
										whileHover={{ x: 4 }}
										onClick={() => loadSession(s.sessionId)}
										className={cn(
											'group flex items-center gap-3 truncate rounded-xl px-4 py-3 text-sm transition-all border border-transparent',
											s.sessionId === sessionId
												? 'bg-primary/10 text-primary border-primary/20 shadow-sm'
												: 'text-muted-foreground hover:bg-muted hover:text-foreground',
										)}
									>
										<Icons.Chat
											className={cn(
												'h-4 w-4 shrink-0 transition-colors',
												s.sessionId === sessionId
													? 'text-primary'
													: 'text-muted-foreground/40 group-hover:text-muted-foreground',
											)}
										/>
										<div className="flex flex-col items-start truncate sm:max-w-[160px]">
											<span className="truncate font-semibold">
												Session_{s.sessionId.slice(0, 8)}
											</span>
											<span className="text-[10px] opacity-60">
												{new Date(s.createdAt).toLocaleDateString(
													undefined,
													{ month: 'short', day: 'numeric' },
												)}
											</span>
										</div>
									</motion.button>
								))
							)}
						</div>
					</div>

					{/* Footer Controls */}
					<div className="pt-6 border-t border-border flex flex-col gap-2">
						<button className="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground">
							<Icons.Settings className="h-4 w-4 opacity-40" />
							Settings
						</button>
						<a
							href="https://github.com/Anurag-Basuri"
							target="_blank"
							rel="noreferrer"
							className="group flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground"
						>
							<Icons.User className="h-4 w-4 opacity-40 transition-colors group-hover:text-primary" />
							Portfolio Access
						</a>
					</div>
				</div>
			</motion.div>
		</>
	);
}
