import { AgentWidget } from '../components/AgentWidget';

export default function HomePage() {
	return (
		<main className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-white">
			<section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-6 py-16 text-center">
				<h1 className="text-4xl font-semibold text-zinc-900">Personal Agent</h1>
				<p className="text-base text-zinc-600">
					Ask anything about Anurag&apos;s portfolio, projects, or reach out directly.
				</p>
			</section>
			<AgentWidget />
		</main>
	);
}
