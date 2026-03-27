'use client';

import { useState, useRef, useEffect } from 'react';
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
		<div className="mx-auto w-full max-w-3xl px-4 pb-6 pt-2">
			<div className="relative flex items-end gap-2 rounded-xl border border-zinc-200 bg-white p-2 shadow-sm transition-shadow focus-within:ring-1 focus-within:ring-emerald-500">
				<textarea
					ref={textareaRef}
					value={text}
					onChange={e => setText(e.target.value)}
					onKeyDown={handleKeyDown}
					placeholder="Message Agent..."
					className="max-h-[200px] min-h-[44px] w-full resize-none border-0 bg-transparent py-3 pl-3 pr-10 text-[15px] focus:ring-0"
					disabled={isTyping}
				/>
				<button
					onClick={handleSubmit}
					disabled={!text.trim() || isTyping}
					className={cn(
						'absolute right-3 bottom-3 flex h-8 w-8 items-center justify-center rounded-md transition',
						text.trim() && !isTyping
							? 'bg-emerald-600 text-white hover:bg-emerald-700'
							: 'bg-zinc-100 text-zinc-400',
					)}
				>
					<Icons.Send className="h-4 w-4" />
				</button>
			</div>
			<div className="mt-2 text-center text-xs text-zinc-400">
				Personal Agent can make mistakes. Verify important technical details.
			</div>
		</div>
	);
}
