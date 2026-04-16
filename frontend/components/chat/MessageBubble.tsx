'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../../store/useAgentStore';
import { cn } from '../../utils/cn';
import { Icons } from '../ui/Icons';
import { ToolCallBadge } from './ToolCallBadge';

export function MessageBubble({ message }: { message: ChatMessage }) {
	const isUser = message.role === 'user';
	const isSystem = message.role === 'system';

	if (isSystem) {
		return (
			<div className="mx-auto my-6 max-w-[90%] rounded-xl bg-rose-500/5 px-6 py-3 text-center text-xs font-bold uppercase tracking-widest text-rose-500 border border-rose-500/20 backdrop-blur-sm">
				<Icons.Warning className="inline-block h-3 w-3 mr-2 -mt-0.5" />
				System: {message.content}
			</div>
		);
	}

	return (
		<div
			className={cn(
				'flex w-full gap-4 py-4 sm:py-6',
				isUser ? 'flex-row-reverse' : 'flex-row',
			)}
		>
			{/* Avatar */}
			<div
				className={cn(
					'flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl shadow-lg transition-transform hover:scale-105',
					isUser
						? 'bg-zinc-800 text-white border border-zinc-700'
						: 'bg-primary text-white animate-glow border border-primary/20',
				)}
			>
				{isUser ? <Icons.User className="h-5 w-5" /> : <Icons.Agent className="h-5 w-5" />}
			</div>

			{/* Bubble Card */}
			<div
				className={cn(
					'flex flex-col gap-2 max-w-[85%] sm:max-w-[75%]',
					isUser ? 'items-end' : 'items-start',
				)}
			>
				<div
					className={cn(
						'flex items-center gap-2 mb-1 px-1',
						isUser ? 'flex-row-reverse' : 'flex-row',
					)}
				>
					<span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground font-display">
						{isUser ? 'User Controller' : 'Neural Agent v2'}
					</span>
				</div>

				<div
					className={cn(
						'relative px-5 py-4 rounded-3xl shadow-sm text-[15px] leading-relaxed',
						isUser
							? 'bg-primary text-white rounded-tr-none font-medium'
							: 'bg-card border border-border rounded-tl-none text-foreground',
					)}
				>
					{/* Markdown Content */}
					<div
						className={cn(
							'prose max-w-none',
							isUser
								? 'prose-invert prose-p:text-white'
								: 'prose-zinc dark:prose-invert',
						)}
					>
						<ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
					</div>

					{/* Tool Executions */}
					{message.toolCalls && message.toolCalls.length > 0 && (
						<div className="flex flex-wrap gap-2 mt-5 pt-4 border-t border-border/50">
							{message.toolCalls.map(tc => (
								<ToolCallBadge key={tc.id} tool={tc} />
							))}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
