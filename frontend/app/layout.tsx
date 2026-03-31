import './globals.css';
import { Fraunces, Space_Grotesk } from 'next/font/google';
import { Providers } from '@/components/auth/Providers';

const spaceGrotesk = Space_Grotesk({
	weight: ['400', '500', '600', '700'],
	subsets: ['latin'],
	variable: '--font-sans',
});

const fraunces = Fraunces({
	weight: ['500', '600', '700'],
	subsets: ['latin'],
	variable: '--font-display',
});

export const metadata = {
	title: 'Personal Agent',
	description: 'Portfolio AI agent',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en" className="scroll-smooth">
			<body className={`${spaceGrotesk.variable} ${fraunces.variable}`}>
				<Providers>{children}</Providers>
			</body>
		</html>
	);
}
