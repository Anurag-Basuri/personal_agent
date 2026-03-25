import ReactMarkdown from 'react-markdown';
import { AgentMessage } from '../types/agent.types';
import { User, Bot } from 'lucide-react';

interface Props {
	message: AgentMessage;
}

export function AgentMessageBubble({ message }: Props) {
	const isUser = message.role === 'user';

	return (
		<div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
			<div
				className={`flex max-w-[85%] gap-3 md:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
			>
				{/* Avatar */}
				<div
					className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full shadow-sm ${
						isUser
							? 'bg-blue-600 text-white'
							: 'bg-emerald-500 text-white ring-2 ring-emerald-500/20'
					}`}
				>
					{isUser ? <User size={16} /> : <Bot size={16} />}
				</div>

				{/* Bubble Body */}
				<div
					className={`flex flex-col rounded-2xl px-4 py-3 text-sm shadow-sm ${
						isUser
							? 'rounded-tr-sm bg-blue-600 text-white'
							: 'rounded-tl-sm bg-white text-zinc-800 border border-zinc-100 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200'
					}`}
				>
					{isUser ? (
						<p className="whitespace-pre-wrap">{message.content}</p>
					) : (
						<div className="prose prose-sm prose-zinc dark:prose-invert max-w-none">
							<ReactMarkdown
								components={{
									a: ({ node, ...props }) => (
										<a
											{...props}
											target="_blank"
											rel="noopener noreferrer"
											className="font-medium text-emerald-600 hover:text-emerald-500 hover:underline dark:text-emerald-400"
										/>
									),
									ul: ({ node, ...props }) => (
										<ul
											{...props}
											className="my-1 ml-4 list-disc space-y-1 marker:text-emerald-500"
										/>
									),
									ol: ({ node, ...props }) => (
										<ol
											{...props}
											className="my-1 ml-4 list-decimal space-y-1 marker:text-emerald-500"
										/>
									),
									strong: ({ node, ...props }) => (
										<strong
											{...props}
											className="font-semibold text-emerald-700 dark:text-emerald-300"
										/>
									),
								}}
							>
								{message.content}
							</ReactMarkdown>
						</div>
					)}
				</div>
			</div>
		</div>
	);
}
