import './globals.css';
import { Inter, Outfit } from 'next/font/google';
import { Providers } from '@/components/auth/Providers';

const inter = Inter({
	subsets: ['latin'],
	variable: '--font-sans',
});

const outfit = Outfit({
	subsets: ['latin'],
	variable: '--font-display',
});

export const metadata = {
	title: 'Personal Agent | Anurag Basuri',
	description:
		'Autonomous AI companion for Anurag Basuri - Portfolio, RAG, and Tool Orchestration.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en" className="scroll-smooth dark">
			<body
				className={`${inter.variable} ${outfit.variable} font-sans antialiased bg-background text-foreground`}
			>
				<Providers>{children}</Providers>
			</body>
		</html>
	);
}
