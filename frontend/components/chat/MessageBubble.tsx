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
			<div className="mx-auto my-4 max-w-[80%] rounded-md bg-rose-50 px-4 py-2 text-center text-sm text-rose-600 border border-rose-100">
				<Icons.Warning className="inline-block h-4 w-4 mr-2 -mt-0.5" />
				{message.content}
			</div>
		);
	}

	return (
		<div className={cn("group relative flex w-full gap-4 px-4 py-6 md:px-0", isUser ? "bg-white" : "bg-zinc-50")}>
			<div className="mx-auto flex w-full max-w-3xl gap-4 md:gap-6">
				{/* Avatar */}
				<div className={cn(
					"flex h-8 w-8 shrink-0 items-center justify-center rounded-sm",
					isUser ? "bg-zinc-800 text-white" : "bg-emerald-600 text-white"
				)}>
					{isUser ? <Icons.User className="h-5 w-5" /> : <Icons.Agent className="h-5 w-5" />}
				</div>

				{/* Content */}
				<div className="flex-1 space-y-4">
					<div className="font-medium text-zinc-900">{isUser ? 'You' : 'Agent'}</div>
					
					{/* Message Text (Markdown) */}
					{message.content && (
						<div className="prose prose-zinc max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-900 prose-pre:text-zinc-100 text-[15px]">
							<ReactMarkdown remarkPlugins={[remarkGfm]}>
								{message.content}
							</ReactMarkdown>
						</div>
					)}

					{/* Tool Calls */}
					{message.toolCalls && message.toolCalls.length > 0 && (
						<div className="flex flex-col gap-2 mt-4">
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
