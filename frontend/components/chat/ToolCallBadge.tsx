import { ToolCall } from '../../store/useAgentStore';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

export function ToolCallBadge({ tool }: { tool: ToolCall }) {
	const isPending = tool.state === 'pending';
	const isError = tool.state === 'error';
	
	return (
		<div className={cn(
			"flex items-center gap-2 rounded-md border px-3 py-2 text-sm",
			isPending ? "border-amber-200 bg-amber-50 text-amber-700" :
			isError ? "border-rose-200 bg-rose-50 text-rose-700" :
			"border-zinc-200 bg-white text-zinc-600"
		)}>
			<Icons.Tool className={cn("h-4 w-4", isPending && "animate-spin text-amber-500")} />
			<span className="font-mono text-xs font-semibold">{tool.name}</span>
			{isPending && <span className="text-xs opacity-70">Running...</span>}
			{isError && <span className="text-xs text-rose-500">Failed</span>}
			{!isPending && !isError && <Icons.Check className="h-4 w-4 text-emerald-500 ml-auto" />}
		</div>
	);
}
