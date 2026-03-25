'use client';

import { Bot, X } from 'lucide-react';
import { AgentWindow } from './AgentWindow';
import { useAgentSession } from '../hooks/useAgentSession';

export function AgentWidget() {
	const session = useAgentSession();
	const { isOpen, setIsOpen } = session;

	return (
		<>
			{/* The Floating Action Button */}
			<button
				onClick={() => setIsOpen(!isOpen)}
				className="group fixed bottom-4 right-4 z-9999 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-600 tracking-wide text-white shadow-lg transition-transform hover:scale-105 hover:bg-emerald-700 active:scale-95 sm:bottom-6 sm:right-6 ring-4 ring-emerald-600/20"
				aria-label="Toggle AI Assistant"
			>
				<div className="relative">
					{isOpen ? (
						<X size={24} className="transition-transform group-hover:rotate-90" />
					) : (
						<Bot
							size={24}
							className="transition-transform group-hover:-translate-y-0.5"
						/>
					)}
					{/* Notification Dot */}
					{!isOpen && (
						<span className="absolute -right-1 -top-1 flex h-3 w-3">
							<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75"></span>
							<span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-400 border-2 border-emerald-600"></span>
						</span>
					)}
				</div>
			</button>

			{/* The Chat Window popup */}
			{isOpen && <AgentWindow {...session} />}
		</>
	);
}
