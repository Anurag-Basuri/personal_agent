'use client';

import { useEffect, useRef } from 'react';
import { useAgentStore } from '../../store/useAgentStore';
import { MessageBubble } from './MessageBubble';

export function ChatArea() {
	const { messages, isTyping } = useAgentStore();
	const bottomRef = useRef<HTMLDivElement>(null);

	// Auto-scroll to bottom when messages change
	useEffect(() => {
		bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages, isTyping]);

	if (messages.length === 0) {
		return (
			<div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
				<div className="relative mb-6">
					<div className="absolute inset-0 rounded-full bg-emerald-200 blur-xl opacity-50" />
					<div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-zinc-200 bg-white shadow-sm">
						<span className="text-3xl">👋</span>
					</div>
				</div>
				<h2 className="text-2xl font-semibold text-zinc-900 mb-2">How can I help you today?</h2>
				<p className="max-w-md text-zinc-500">
					Ask me about Anurag's projects, technical skills, or have me write an email to him.
				</p>
			</div>
		);
	}

	return (
		<div className="flex-1 overflow-y-auto pb-6">
			{messages.map((msg) => (
				<MessageBubble key={msg.id} message={msg} />
			))}
			
			{isTyping && (
				<div className="group relative flex w-full gap-4 px-4 py-6 bg-zinc-50 md:px-0">
					<div className="mx-auto flex w-full max-w-3xl gap-4 md:gap-6">
						<div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-emerald-600 text-white">
							<span className="h-2 w-2 rounded-full bg-white animate-bounce" />
						</div>
						<div className="flex-1 space-y-4">
							<div className="font-medium text-zinc-900">Agent</div>
							<div className="flex items-center gap-1 mt-2">
								<span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: '0ms' }} />
								<span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: '150ms' }} />
								<span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-bounce" style={{ animationDelay: '300ms' }} />
							</div>
						</div>
					</div>
				</div>
			)}
			<div ref={bottomRef} className="h-4" />
		</div>
	);
}
