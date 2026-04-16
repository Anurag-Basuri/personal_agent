'use client';

import { motion, AnimatePresence, Variants } from 'framer-motion';
import { AuthButton } from '@/components/auth/AuthButton';
import { Icons } from '@/components/ui/Icons';
import { useSession } from 'next-auth/react';
import Link from 'next/link';

const containerVariants: Variants = {
	hidden: { opacity: 0 },
	visible: {
		opacity: 1,
		transition: { staggerChildren: 0.15, delayChildren: 0.2 },
	},
};

const itemVariants: Variants = {
	hidden: { opacity: 0, y: 30 },
	visible: {
		opacity: 1,
		y: 0,
		transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
	},
};

export default function LandingPage() {
	const { data: session } = useSession();

	return (
		<div className="relative min-h-screen bg-background selection:bg-primary/30 overflow-x-hidden">
			{/* Animated Background */}
			<div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
				<div className="mesh-gradient absolute inset-0 opacity-60" />
				<motion.div
					animate={{
						scale: [1, 1.1, 1],
						opacity: [0.3, 0.5, 0.3],
					}}
					transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
					className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[120px]"
				/>
				<motion.div
					animate={{
						scale: [1, 1.2, 1],
						opacity: [0.2, 0.4, 0.2],
					}}
					transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
					className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[100px]"
				/>
			</div>

			{/* Navbar */}
			<motion.nav
				initial={{ y: -100 }}
				animate={{ y: 0 }}
				transition={{ type: 'spring', damping: 20, stiffness: 100 }}
				className="fixed left-0 right-0 top-0 z-50 flex justify-center pt-6 px-6 pointer-events-none"
			>
				<div className="glass flex h-14 w-full max-w-5xl items-center justify-between gap-6 rounded-full px-6 py-2 shadow-2xl pointer-events-auto">
					<div className="flex items-center gap-3">
						<div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white shadow-lg animate-glow">
							<Icons.Agent className="h-5 w-5" />
						</div>
						<span className="font-display text-lg font-bold tracking-tight text-foreground hidden sm:block">
							Personal Agent
						</span>
					</div>
					<div className="flex items-center gap-4">
						<AnimatePresence>
							{session && (
								<motion.div
									initial={{ opacity: 0, x: 20 }}
									animate={{ opacity: 1, x: 0 }}
									exit={{ opacity: 0, x: 20 }}
								>
									<Link
										href="/chat"
										className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors pr-4"
									>
										Console &rarr;
									</Link>
								</motion.div>
							)}
						</AnimatePresence>
						<AuthButton className="rounded-full px-5 h-9 text-xs" />
					</div>
				</div>
			</motion.nav>

			{/* Hero Section */}
			<main className="relative z-10 mx-auto max-w-7xl pt-40 pb-20 px-6">
				<motion.div
					variants={containerVariants}
					initial="hidden"
					animate="visible"
					className="flex flex-col items-center gap-8 text-center"
				>
					<motion.div variants={itemVariants}>
						<span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary shadow-sm backdrop-blur-sm">
							<span className="relative flex h-2 w-2">
								<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
								<span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
							</span>
							Agentic Core 2.0
						</span>
					</motion.div>

					<motion.h1
						variants={itemVariants}
						className="font-display text-6xl font-black tracking-tight text-foreground sm:text-8xl lg:leading-[1.05]"
					>
						Your Intelligence, <br />
						<span className="text-primary italic">Amplified.</span>
					</motion.h1>

					<motion.p
						variants={itemVariants}
						className="max-w-2xl text-lg text-muted-foreground leading-relaxed text-balance"
					>
						An autonomous ecosystem designed to master your context. From technical
						deep-dives to seamless tool orchestration, the future of productivity is
						here.
					</motion.p>

					<motion.div
						variants={itemVariants}
						className="mt-4 flex flex-col items-center gap-5 sm:flex-row"
					>
						{session ? (
							<Link
								href="/chat"
								className="group flex h-14 w-full items-center justify-center gap-3 rounded-full bg-primary px-10 text-base font-bold text-white shadow-[0_20px_50px_rgba(16,185,129,0.2)] transition active:scale-95 hover:bg-primary/90 sm:w-auto"
							>
								Launch Console
								<Icons.Send className="h-4 w-4 transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
							</Link>
						) : (
							<AuthButton className="h-14 px-10 text-base rounded-full shadow-2xl" />
						)}
						<a
							href="https://github.com/Anurag-Basuri"
							target="_blank"
							rel="noreferrer"
							className="flex h-14 w-full items-center justify-center gap-2 rounded-full border border-border bg-card/50 backdrop-blur-sm px-10 text-base font-bold text-foreground transition hover:bg-accent sm:w-auto"
						>
							Portfolio
						</a>
					</motion.div>
				</motion.div>

				{/* Features Grid */}
				<motion.div
					initial={{ opacity: 0, y: 100 }}
					whileInView={{ opacity: 1, y: 0 }}
					viewport={{ once: true, margin: '-100px' }}
					transition={{ duration: 0.8 }}
					className="mt-40 grid gap-6 md:grid-cols-3"
				>
					{[
						{
							icon: <Icons.Tool className="h-6 w-6 text-primary" />,
							title: 'Tool Orchestration',
							desc: 'Autonomous execution of GitHub fetches, API interactions, and complex pipeline logic with precision.',
						},
						{
							icon: <Icons.Check className="h-6 w-6 text-primary" />,
							title: 'Contextual RAG',
							desc: 'Dynamic ingestion of resume, skill, and project data to provide highly personalized technical responses.',
						},
						{
							icon: <Icons.User className="h-6 w-6 text-primary" />,
							title: 'Omni-Memory',
							desc: 'Cross-transport persistence that remembers your preferences across Web and Telegram interfaces.',
						},
					].map((feat, i) => (
						<motion.div
							key={i}
							whileHover={{ y: -10 }}
							className="group relative overflow-hidden rounded-3xl border border-border bg-card/40 p-10 backdrop-blur-sm transition-all hover:bg-card/60 hover:shadow-2xl hover:shadow-primary/5"
						>
							<div className="absolute top-0 right-0 -mr-10 -mt-10 h-32 w-32 bg-primary/5 rounded-full blur-[40px] transition-all group-hover:bg-primary/10" />
							<div className="mb-8 inline-flex rounded-2xl bg-primary/10 p-4 ring-1 ring-primary/20">
								{feat.icon}
							</div>
							<h3 className="mb-4 text-xl font-bold text-foreground">{feat.title}</h3>
							<p className="text-sm leading-relaxed text-muted-foreground">
								{feat.desc}
							</p>
						</motion.div>
					))}
				</motion.div>
			</main>
		</div>
	);
}
