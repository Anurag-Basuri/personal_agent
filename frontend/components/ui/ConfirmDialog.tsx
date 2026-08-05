'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Icons } from './Icons';

interface ConfirmDialogProps {
	isOpen: boolean;
	title: string;
	message: string;
	confirmText?: string;
	cancelText?: string;
	onConfirm: () => void;
	onCancel: () => void;
	isDestructive?: boolean;
}

export function ConfirmDialog({
	isOpen,
	title,
	message,
	confirmText = 'Confirm',
	cancelText = 'Cancel',
	onConfirm,
	onCancel,
	isDestructive = false,
}: ConfirmDialogProps) {
	return (
		<AnimatePresence>
			{isOpen && (
				<>
					{/* Backdrop */}
					<motion.div
						initial={{ opacity: 0 }}
						animate={{ opacity: 1 }}
						exit={{ opacity: 0 }}
						onClick={onCancel}
						className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
					/>
					{/* Dialog */}
					<div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
						<motion.div
							initial={{ opacity: 0, scale: 0.95, y: 10 }}
							animate={{ opacity: 1, scale: 1, y: 0 }}
							exit={{ opacity: 0, scale: 0.95, y: 10 }}
							className="w-full max-w-md overflow-hidden rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-white/10 shadow-2xl pointer-events-auto"
						>
							<div className="p-6">
								<div className="flex items-center gap-3 mb-4">
									<div
										className={`flex h-10 w-10 items-center justify-center rounded-full ${
											isDestructive
												? 'bg-destructive/10 text-destructive'
												: 'bg-primary/10 text-primary'
										}`}
									>
										{isDestructive ? <Icons.Warning className="h-5 w-5" /> : <Icons.Settings className="h-5 w-5" />}
									</div>
									<h2 className="text-xl font-bold text-foreground font-display tracking-tight">
										{title}
									</h2>
								</div>
								<p className="text-muted-foreground mb-6 font-medium leading-relaxed text-sm">
									{message}
								</p>
								<div className="flex gap-3 justify-end">
									<button
										onClick={onCancel}
										className="rounded-lg px-4 py-2 font-medium text-muted-foreground hover:bg-zinc-100 dark:hover:bg-muted transition-colors focus-ring outline-none"
									>
										{cancelText}
									</button>
									<button
										onClick={() => {
											onConfirm();
											onCancel(); // auto-close on confirm
										}}
										className={`rounded-lg px-4 py-2 font-bold text-white shadow-md transition-transform active:scale-95 focus-ring outline-none ${
											isDestructive
												? 'bg-destructive hover:bg-destructive/90 shadow-destructive/20'
												: 'bg-primary hover:bg-primary/90 shadow-primary/20'
										}`}
									>
										{confirmText}
									</button>
								</div>
							</div>
						</motion.div>
					</div>
				</>
			)}
		</AnimatePresence>
	);
}
