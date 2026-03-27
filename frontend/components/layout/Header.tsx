'use client';

import { useAgentStore } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';

export function Header() {
	const { isSidebarOpen, setSidebarOpen } = useAgentStore();

	return (
		<header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-zinc-200 bg-white/80 px-4 backdrop-blur-md">
			<div className="flex items-center gap-3">
				<button 
					onClick={() => setSidebarOpen(!isSidebarOpen)} 
					className="p-2 -ml-2 rounded-md hover:bg-zinc-100 text-zinc-600 transition"
				>
					<Icons.Menu className="h-5 w-5" />
				</button>
				<span className="font-semibold text-zinc-800">Personal Agent</span>
			</div>
			<div className="flex items-center gap-2">
				<div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
				<span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Online</span>
			</div>
		</header>
	);
}
