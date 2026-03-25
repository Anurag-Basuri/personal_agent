import './globals.css';

export const metadata = {
	title: 'Personal Agent',
	description: 'Portfolio AI agent',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html lang="en">
			<body>{children}</body>
		</html>
	);
}
