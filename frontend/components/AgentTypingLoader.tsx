export function AgentTypingLoader() {
	return (
		<div className="flex w-fit items-center self-start rounded-2xl bg-zinc-800 px-4 py-3 text-sm text-zinc-100 dark:bg-zinc-800 dark:text-zinc-100">
			<div className="flex items-center gap-1.5">
				<div
					className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400"
					style={{ animationDelay: '0ms' }}
				/>
				<div
					className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400"
					style={{ animationDelay: '150ms' }}
				/>
				<div
					className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400"
					style={{ animationDelay: '300ms' }}
				/>
			</div>
		</div>
	);
}
