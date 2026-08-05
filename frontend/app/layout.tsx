import './globals.css';
import { Inter, Outfit, JetBrains_Mono } from 'next/font/google';
import { Providers } from '@/components/auth/Providers';
import type { Metadata } from 'next';

const inter = Inter({
	subsets: ['latin'],
	variable: '--font-sans',
	display: 'swap',
});

const outfit = Outfit({
	subsets: ['latin'],
	variable: '--font-display',
	display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
	subsets: ['latin'],
	variable: '--font-mono',
	display: 'swap',
});

export const metadata: Metadata = {
	title: "Anurag's Cortex",
	description:
		'An autonomous AI agent with tool orchestration, contextual RAG, and omni-memory — built for software engineers.',
	keywords: ['AI Agent', 'Portfolio', 'RAG', 'LangGraph', 'Anurag Basuri', 'Cortex'],
	authors: [{ name: 'Anurag Basuri', url: 'https://github.com/Anurag-Basuri' }],
	openGraph: {
		title: "Anurag's Cortex",
		description: 'Autonomous AI companion with tool calling, RAG, and multi-transport support.',
		type: 'website',
	},
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
			<head>
				<script
					dangerouslySetInnerHTML={{
						__html: `
							(function() {
								try {
									var theme = localStorage.getItem('theme');
									if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
										document.documentElement.classList.add('dark');
									} else {
										document.documentElement.classList.remove('dark');
									}
								} catch(e) {}
							})();
						`,
					}}
				/>
			</head>
			<body
				suppressHydrationWarning
				className={`${inter.variable} ${outfit.variable} ${jetbrainsMono.variable} font-sans antialiased bg-background text-foreground`}
			>
				<Providers>{children}</Providers>
			</body>
		</html>
	);
}
