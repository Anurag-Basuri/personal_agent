'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { useAgentStore } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

export function Composer() {
	const [text, setText] = useState('');
	const textareaRef = useRef<HTMLTextAreaElement>(null);
	const { sendMessage } = useAgentAPI();
	const { isTyping } = useAgentStore();

	// Auto-resize textarea
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = 'auto';
			textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
		}
	}, [text]);

	const handleSubmit = () => {
		if (!text.trim() || isTyping) return;
		sendMessage(text.trim());
		setText('');
		if (textareaRef.current) {
			textareaRef.current.style.height = 'auto';
		}
	};

	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	};

	return (
		<div className="mx-auto w-full max-w-3xl px-6 pb-8 pt-2">
			<div className="relative flex items-end gap-2 p-2 rounded-[28px] border border-border bg-card/50 backdrop-blur-xl shadow-2xl transition-all focus-within:ring-2 focus-within:ring-primary/40 focus-within:border-primary/50 group">
				<textarea
					ref={textareaRef}
					value={text}
					onChange={e => setText(e.target.value)}
					onKeyDown={handleKeyDown}
					placeholder="Message Neural Agent..."
					className="max-h-[200px] min-h-[48px] w-full resize-none border-0 bg-transparent py-3.5 pl-5 pr-12 text-[15px] focus:ring-0 placeholder:text-muted-foreground/50 transition-all font-medium"
					disabled={isTyping}
				/>

				<AnimatePresence>
					{text.trim() && !isTyping && (
						<motion.button
							initial={{ scale: 0.8, opacity: 0 }}
							animate={{ scale: 1, opacity: 1 }}
							exit={{ scale: 0.8, opacity: 0 }}
							onClick={handleSubmit}
							className="absolute right-3.5 bottom-3.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-white shadow-lg animate-glow hover:bg-primary/90 transition-all active:scale-90"
						>
							<Icons.Send className="h-5 w-5" />
						</motion.button>
					)}
				</AnimatePresence>

				{!text.trim() && (
					<div className="absolute right-3.5 bottom-3.5 flex h-10 w-10 items-center justify-center rounded-2xl bg-muted/50 text-muted-foreground/40 border border-border/50">
						<Icons.Send className="h-4 w-4" />
					</div>
				)}
			</div>

			<motion.div
				initial={{ opacity: 0 }}
				animate={{ opacity: 1 }}
				transition={{ delay: 1 }}
				className="mt-4 text-center px-4"
			>
				<p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/40 font-display">
					Secure Workspace &bull; RAG Context Active &bull; AES-GCM Encrypted
				</p>
			</motion.div>
		</div>
	);
}
