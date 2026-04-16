'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentStore } from '../../store/useAgentStore';
import { MessageBubble } from './MessageBubble';
import { Icons } from '../ui/Icons';

export function ChatArea() {
	const { messages, isTyping } = useAgentStore();
	const bottomRef = useRef<HTMLDivElement>(null);

	// Auto-scroll to bottom when messages change
	useEffect(() => {
		bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [messages, isTyping]);

	if (messages.length === 0) {
		return (
			<motion.div
				initial={{ opacity: 0, scale: 0.9 }}
				animate={{ opacity: 1, scale: 1 }}
				className="flex flex-1 flex-col items-center justify-center p-8 text-center"
			>
				<div className="relative mb-10 group">
					<div className="absolute inset-0 rounded-full bg-primary/20 blur-3xl opacity-50 group-hover:opacity-80 transition-opacity" />
					<div className="relative flex h-24 w-24 items-center justify-center rounded-3xl border border-primary/20 bg-card shadow-2xl animate-glow">
						<Icons.Agent className="h-10 w-10 text-primary" />
					</div>
				</div>
				<h2 className="text-3xl font-black text-foreground mb-4 font-display">
					Ready to assist, Captain.
				</h2>
				<p className="max-w-md text-muted-foreground text-sm leading-relaxed">
					Ask me about your technical roadmap, RAG-indexed portfolio data, or have me
					trigger external tool workflows.
				</p>
			</motion.div>
		);
	}

	return (
		<div className="flex-1 overflow-y-auto px-4 md:px-0">
			<div className="mx-auto max-w-3xl w-full py-10 space-y-2">
				<AnimatePresence initial={false}>
					{messages.map((msg, index) => (
						<motion.div
							key={msg.id || index}
							initial={{ opacity: 0, y: 20, scale: 0.95 }}
							animate={{ opacity: 1, y: 0, scale: 1 }}
							exit={{ opacity: 0, transition: { duration: 0.2 } }}
							transition={{ type: 'spring', damping: 25, stiffness: 200 }}
						>
							<MessageBubble message={msg} />
						</motion.div>
					))}
				</AnimatePresence>

				{isTyping && (
					<motion.div
						initial={{ opacity: 0, y: 10 }}
						animate={{ opacity: 1, y: 0 }}
						className="flex gap-4 p-6"
					>
						<div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary">
							<Icons.Agent className="h-5 w-5" />
						</div>
						<div className="flex items-center gap-1.5 px-4 py-2 bg-muted/30 rounded-2xl rounded-tl-none border border-border">
							<motion.span
								animate={{ scale: [1, 1.3, 1] }}
								transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
								className="h-1.5 w-1.5 rounded-full bg-primary/60"
							/>
							<motion.span
								animate={{ scale: [1, 1.3, 1] }}
								transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
								className="h-1.5 w-1.5 rounded-full bg-primary/60"
							/>
							<motion.span
								animate={{ scale: [1, 1.3, 1] }}
								transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
								className="h-1.5 w-1.5 rounded-full bg-primary/60"
							/>
						</div>
					</motion.div>
				)}
				<div ref={bottomRef} className="h-20" />
			</div>
		</div>
	);
}
