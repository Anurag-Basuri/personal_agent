'use client';

import { useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

export function Sidebar() {
	const { isSidebarOpen, setSidebarOpen, sessions, sessionId, setSessionId, resetChat } = useAgentStore();
	const { fetchSessions, resetSession } = useAgentAPI();

	useEffect(() => {
		fetchSessions();
	}, [fetchSessions]);

	const handleNewChat = useCallback(async () => {
		await resetSession(); // Server-side reset
		resetChat(); // Client-side reset
		setSessionId(crypto.randomUUID());
		if (window.innerWidth < 768) {
			setSidebarOpen(false);
		}
	}, [resetSession, resetChat, setSessionId, setSidebarOpen]);

	const loadSession = useCallback((id: string) => {
		setSessionId(id);
		// In a real app we'd fetch actual history for this session here.
		// For now we just switch the ID.
		if (window.innerWidth < 768) {
			setSidebarOpen(false);
		}
	}, [setSessionId, setSidebarOpen]);

	return (
		<>
			{/* Mobile Overlay */}
			<AnimatePresence>
				{isSidebarOpen && (
					<motion.div
						initial={{ opacity: 0 }}
						animate={{ opacity: 0.5 }}
						exit={{ opacity: 0 }}
						onClick={() => setSidebarOpen(false)}
						className="fixed inset-0 z-40 bg-zinc-900/50 md:hidden"
					/>
				)}
			</AnimatePresence>

			{/* Sidebar */}
			<motion.div
				initial={false}
				animate={{ width: isSidebarOpen ? 280 : 0 }}
				className={cn(
					"fixed inset-y-0 left-0 z-50 flex h-full flex-col overflow-hidden bg-zinc-900 text-zinc-300 md:relative",
					!isSidebarOpen && "md:w-0"
				)}
			>
				<div className="flex h-full w-[280px] flex-col p-4">
					<button
						onClick={handleNewChat}
						className="flex items-center gap-3 rounded-lg border border-zinc-700 p-3 text-sm transition hover:bg-zinc-800 hover:text-white"
					>
						<Icons.Add className="h-4 w-4" />
						New Chat
					</button>

					<div className="mt-8 flex-1 overflow-y-auto">
						<div className="mb-2 px-2 text-xs font-semibold text-zinc-500">RECENT SESSIONS</div>
						<div className="flex flex-col gap-1">
							{sessions.map((s) => (
								<button
									key={s.id}
									onClick={() => loadSession(s.sessionId)}
									className={cn(
										"flex items-center gap-3 truncate rounded-md px-3 py-2 text-sm transition hover:bg-zinc-800 hover:text-white",
										s.sessionId === sessionId && "bg-zinc-800 text-white"
									)}
								>
									<Icons.Chat className="h-4 w-4 shrink-0" />
									<span className="truncate">{new Date(s.createdAt).toLocaleDateString()} Chat</span>
								</button>
							))}
						</div>
					</div>

					<div className="mt-auto border-t border-zinc-800 pt-4">
						<button className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition hover:bg-zinc-800 hover:text-white">
							<Icons.Settings className="h-4 w-4" />
							Settings
						</button>
						<a 
							href="https://anuragbasuri.com" 
							target="_blank"
							rel="noreferrer"
							className="mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition hover:bg-zinc-800 hover:text-white"
						>
							<Icons.User className="h-4 w-4" />
							Portfolio
						</a>
					</div>
				</div>
			</motion.div>
		</>
	);
}
