'use client';

import { AgentWindow } from '../components/AgentWindow';
import { useAgentSession } from '../hooks/useAgentSession';

export default function HomePage() {
	const session = useAgentSession();

	return (
		<main className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.25),_transparent_52%),linear-gradient(180deg,_rgba(248,250,252,1),_rgba(226,232,240,1))]">
			<div className="pointer-events-none absolute -top-24 left-1/2 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-emerald-200/40 blur-3xl" />
			<div className="pointer-events-none absolute bottom-[-160px] right-[-80px] h-[360px] w-[360px] rounded-full bg-sky-200/50 blur-3xl" />

			<section className="relative mx-auto flex max-w-5xl flex-col items-center gap-6 px-6 py-16 text-center">
				<span className="rounded-full border border-emerald-200/70 bg-white/70 px-4 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700 shadow-sm">
					Portfolio AI
				</span>
				<h1 className="font-display text-4xl font-semibold text-zinc-900 sm:text-5xl">
					Meet Anurag&apos;s Personal Agent
				</h1>
				<p className="max-w-2xl text-base text-zinc-600">
					Ask about projects, skills, and availability. The assistant can also connect you
					directly with Anurag.
				</p>
			</section>

			<section className="relative mx-auto flex max-w-5xl justify-center px-6 pb-20">
				<AgentWindow {...session} isOpen variant="centered" />
			</section>
		</main>
	);
}
