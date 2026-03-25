import { useRef, useEffect } from 'react';
import { Send, X, Bot, Trash2 } from 'lucide-react';
import { useAgentSession } from '../hooks/useAgentSession';
import { AgentMessageBubble } from './AgentMessageBubble';
import { AgentTypingLoader } from './AgentTypingLoader';
import { AgentMessage } from '../types/agent.types';

export interface AgentWindowProps {
	messages: AgentMessage[];
	isLoading: boolean;
	isOpen: boolean;
	setIsOpen: (val: boolean) => void;
	sendMessage: (val: string) => void;
	clearSession: () => void;
	variant?: 'floating' | 'centered';
}

export function AgentWindow({
	messages,
	isLoading,
	isOpen,
	setIsOpen,
	sendMessage,
	clearSession,
	variant = 'floating',
}: AgentWindowProps) {
	const inputRef = useRef<HTMLInputElement>(null);
	const scrollRef = useRef<HTMLDivElement>(null);

	// Auto-scroll to bottom
	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
		}
	}, [messages, isLoading, isOpen]);

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		const val = inputRef.current?.value.trim();
		if (!val) return;
		sendMessage(val);
		if (inputRef.current) inputRef.current.value = '';
	};

	if (!isOpen && variant === 'floating') return null;

	const wrapperClass =
		variant === 'centered'
			? 'relative flex h-[680px] w-full max-w-[900px] flex-col overflow-hidden rounded-3xl bg-white/90 shadow-2xl ring-1 ring-emerald-200/50 backdrop-blur-lg'
			: 'fixed bottom-20 right-4 z-9999 flex h-[500px] w-[350px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-zinc-200 transition-all dark:bg-zinc-950 dark:ring-zinc-800 sm:bottom-24 sm:right-6 sm:h-[550px] sm:w-[380px]';

	return (
		<div className={wrapperClass}>
			{/* Header */}
			<div className="flex items-center justify-between border-b border-zinc-100 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
				<div className="flex items-center gap-2">
					<div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-white">
						<Bot size={18} />
					</div>
					<div>
						<h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
							AI Assistant
						</h3>
						<p className="text-xs text-emerald-600 dark:text-emerald-500">
							Powered by LangChain
						</p>
					</div>
				</div>
				<div className="flex items-center gap-1">
					<button
						onClick={clearSession}
						className="rounded-full p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-colors dark:hover:bg-zinc-900 dark:hover:text-zinc-300"
						title="Clear Conversation"
					>
						<Trash2 size={16} />
					</button>
					{variant === 'floating' && (
						<button
							onClick={() => setIsOpen(false)}
							className="rounded-full p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 transition-colors dark:hover:bg-zinc-900 dark:hover:text-zinc-300"
						>
							<X size={18} />
						</button>
					)}
				</div>
			</div>

			{/* Message List */}
			<div
				ref={scrollRef}
				className="flex-1 overflow-y-auto bg-zinc-50/50 p-4 dark:bg-zinc-900/50"
			>
				{messages.length === 0 ? (
					<div className="flex h-full flex-col items-center justify-center space-y-3 text-center opacity-70">
						<div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400">
							<Bot size={24} />
						</div>
						<div className="space-y-1">
							<p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
								Hi there!
							</p>
							<p className="text-xs text-zinc-500 dark:text-zinc-400 max-w-[200px]">
								I can answer questions about Anurag's projects, LeetCode stats, or
								schedule a meeting.
							</p>
						</div>
					</div>
				) : (
					<div className="flex flex-col gap-1">
						{messages.map(msg => (
							<AgentMessageBubble key={msg.id} message={msg} />
						))}
						{isLoading && <AgentTypingLoader />}
					</div>
				)}
			</div>

			{/* Input Area */}
			<div className="border-t border-zinc-100 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950">
				<form onSubmit={handleSubmit} className="flex items-center gap-2">
					<input
						ref={inputRef}
						disabled={isLoading}
						type="text"
						placeholder={isLoading ? 'Thinking... 💡' : 'Ask me anything...'}
						className="flex-1 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2 text-sm text-zinc-900 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-emerald-500 dark:focus:ring-emerald-500"
					/>
					<button
						type="submit"
						disabled={isLoading}
						className="group flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white transition-all hover:bg-emerald-700 active:scale-95 disabled:bg-zinc-300 disabled:active:scale-100 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
					>
						<Send
							size={16}
							className="ml-[-2px] transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
						/>
					</button>
				</form>
			</div>
		</div>
	);
}
