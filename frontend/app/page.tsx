import { AuthButton } from '@/components/auth/AuthButton';
import { Icons } from '@/components/ui/Icons';
import { auth } from '@/auth';
import Link from 'next/link';

export default async function LandingPage() {
	const session = await auth();

	return (
		<div className="relative min-h-screen bg-white">
			{/* Navbar */}
			<nav className="fixed left-0 right-0 top-0 z-50 border-b border-zinc-200/80 bg-white/70 backdrop-blur-md">
				<div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
					<div className="flex items-center gap-2">
						<div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white">
							<Icons.Agent className="h-5 w-5" />
						</div>
						<span className="font-display text-xl font-semibold tracking-tight text-zinc-900">
							Personal Agent
						</span>
					</div>
					<div className="flex items-center gap-4">
						{session ? (
							<Link
								href="/chat"
								className="text-sm font-medium text-emerald-700 hover:text-emerald-800 transition"
							>
								Go to Chat &rarr;
							</Link>
						) : null}
						<AuthButton />
					</div>
				</div>
			</nav>

			{/* Hero Section */}
			<section className="relative overflow-hidden pt-32 pb-20 lg:pt-48 lg:pb-32">
				{/* Background Gradients */}
				<div className="pointer-events-none absolute -top-40 left-1/2 h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-emerald-100/50 blur-[100px]" />
				<div className="pointer-events-none absolute right-[-200px] top-[20%] h-[400px] w-[600px] rounded-full bg-sky-100/40 blur-[80px]" />

				<div className="relative mx-auto flex max-w-5xl flex-col items-center gap-8 px-6 text-center">
					<span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-emerald-800 shadow-sm">
						<span className="relative flex h-2 w-2">
							<span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
							<span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
						</span>
						Agentic Core 2.0 Live
					</span>

					<h1 className="font-display text-5xl font-bold tracking-tight text-zinc-900 sm:text-7xl lg:leading-[1.1]">
						Your Intelligence, <br />
						<span className="text-emerald-600">Amplified.</span>
					</h1>

					<p className="max-w-2xl text-lg text-zinc-600 sm:text-xl">
						Experience a fully autonomous AI agent designed to assist with scheduling,
						portfolio research, technical breakdowns, and deep integration with Anurag's workflow.
					</p>

					<div className="mt-4 flex flex-col items-center gap-4 sm:flex-row">
						{session ? (
							<Link
								href="/chat"
								className="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-emerald-600 px-8 text-base font-semibold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700 hover:shadow-emerald-600/30 sm:w-auto"
							>
								Enter Agent Console
								<Icons.Send className="h-4 w-4" />
							</Link>
						) : (
							<AuthButton className="h-12 px-8 text-base" />
						)}
						<a
							href="https://github.com/Anurag-Basuri"
							target="_blank"
							rel="noreferrer"
							className="flex h-12 w-full items-center justify-center gap-2 rounded-full border border-zinc-200 bg-white px-8 text-base font-medium text-zinc-700 transition hover:bg-zinc-50 sm:w-auto"
						>
							View Portfolio
						</a>
					</div>
				</div>
			</section>

			{/* Features / Value Proposition */}
			<section className="border-t border-zinc-100 bg-zinc-50/50 py-20 lg:py-32">
				<div className="mx-auto max-w-7xl px-6">
					<div className="mb-16 text-center">
						<h2 className="font-display text-3xl font-bold text-zinc-900 sm:text-4xl">
							Built with cutting-edge tech.
						</h2>
						<p className="mt-4 text-zinc-600">
							Powered by FastAPI, LangChain, and Next.js 15.
						</p>
					</div>

					<div className="grid gap-8 md:grid-cols-3">
						{[
							{
								icon: <Icons.Tool className="h-6 w-6 text-sky-600" />,
								title: 'Tool Orchestration',
								desc: 'The agent securely executes external API calls, GitHub fetches, and custom pipeline workflows on your behalf.',
							},
							{
								icon: <Icons.Check className="h-6 w-6 text-emerald-600" />,
								title: 'Advanced RAG',
								desc: 'Ingests deep context to accurately reflect skills, resume data, and project timelines dynamically.',
							},
							{
								icon: <Icons.User className="h-6 w-6 text-indigo-600" />,
								title: 'Secure Authentication',
								desc: 'Your sessions and context are securely walled behind Google OAuth2, ensuring isolated workflows.',
							},
						].map((feat, i) => (
							<div
								key={i}
								className="group rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm transition hover:shadow-md"
							>
								<div className="mb-6 inline-flex rounded-xl bg-zinc-50 p-3 ring-1 ring-zinc-100 group-hover:bg-white group-hover:ring-zinc-200">
									{feat.icon}
								</div>
								<h3 className="mb-3 text-lg font-semibold text-zinc-900">{feat.title}</h3>
								<p className="text-sm leading-relaxed text-zinc-600">{feat.desc}</p>
							</div>
						))}
					</div>
				</div>
			</section>
		</div>
	);
}
